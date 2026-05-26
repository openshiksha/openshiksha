"""
Tests for user profile update endpoint.

Covers PATCH /api/v1/users/me/profile/
"""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.test import APIClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Profile Test School", board=board)


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="profile_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        first_name="Old",
        last_name="Name",
        email="old@test.com",
    )


@pytest.fixture
def student2(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(
        username="profile_student2",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        email="taken@test.com",
    )


@pytest.fixture
def authed_client(student):
    client = APIClient()
    refresh = RefreshToken.for_user(student)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_student_can_update_own_name(authed_client, student):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"first_name": "New", "last_name": "Updated"},
        format="json",
    )
    assert res.status_code == 200
    data = res.json()
    assert data["first_name"] == "New"
    assert data["last_name"] == "Updated"
    student.refresh_from_db()
    assert student.first_name == "New"


def test_student_can_update_own_email(authed_client, student):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"email": "newemail@test.com"},
        format="json",
    )
    assert res.status_code == 200
    student.refresh_from_db()
    assert student.email == "newemail@test.com"


def test_student_cannot_change_own_role(authed_client, student):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"role": "teacher"},
        format="json",
    )
    assert res.status_code == 200
    student.refresh_from_db()
    assert student.role == "student"


def test_partial_update_preserves_unchanged_fields(authed_client, student):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"first_name": "Partial"},
        format="json",
    )
    assert res.status_code == 200
    student.refresh_from_db()
    assert student.first_name == "Partial"
    assert student.last_name == "Name"
    assert student.email == "old@test.com"


def test_invalid_email_returns_400(authed_client):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"email": "not-an-email"},
        format="json",
    )
    assert res.status_code == 400


def test_duplicate_email_returns_400(authed_client, student2):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"email": "taken@test.com"},
        format="json",
    )
    assert res.status_code == 400


def test_unauthenticated_returns_401(db):
    client = APIClient()
    res = client.patch("/api/v1/users/me/profile/", {"first_name": "Hack"}, format="json")
    assert res.status_code == 401


def test_student_can_update_phone_number(authed_client, student):
    res = authed_client.patch(
        "/api/v1/users/me/profile/",
        {"phone_number": "+91 9876543210"},
        format="json",
    )
    assert res.status_code == 200
    student.refresh_from_db()
    assert student.phone_number == "+91 9876543210"
