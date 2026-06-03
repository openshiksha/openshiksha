"""
Tests for self-service registration endpoints.

Covers:
  POST /api/v1/auth/register/open/   — open student registration
  POST /api/v1/auth/register/school/ — school student registration via join code
"""

import pytest

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

    return School.objects.create(name="Reg Test School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=8, description="Grade 8")


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="reg_teacher", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def classroom(db, school, standard, teacher):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(
        school=school, standard=standard, division="A", class_teacher=teacher, academic_year="2024-25"
    )


@pytest.fixture
def subject_room(db, classroom, subject, teacher):
    from openshiksha.apps.core.models import SubjectRoom

    return SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher, is_active=True)


@pytest.fixture
def invite_code(db, classroom, teacher):
    from openshiksha.apps.core.models import ClassroomInviteCode

    return ClassroomInviteCode.objects.create(classroom=classroom, code="ABC123", created_by=teacher, is_active=True)


@pytest.fixture
def client():
    return APIClient()


# ---------------------------------------------------------------------------
# Open Student Registration
# ---------------------------------------------------------------------------


def test_open_student_registration_creates_account(client, db):
    res = client.post(
        "/api/v1/auth/register/open/",
        {"username": "newopen", "password": "strongpass123", "email": "newopen@test.com", "first_name": "New"},
        format="json",
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "open_student"
    assert data["user"]["username"] == "newopen"
    assert "access" in data
    assert "refresh" in data


def test_open_student_registration_returns_jwt(client, db):
    res = client.post(
        "/api/v1/auth/register/open/",
        {"username": "jwttest_open", "password": "strongpass123"},
        format="json",
    )
    assert res.status_code == 201
    data = res.json()
    assert len(data["access"]) > 20


def test_duplicate_username_returns_400(client, db):
    from openshiksha.apps.core.models import User, UserRole

    User.objects.create_user(username="taken_user", password="pass", role=UserRole.OPEN_STUDENT)
    res = client.post(
        "/api/v1/auth/register/open/",
        {"username": "taken_user", "password": "strongpass123"},
        format="json",
    )
    assert res.status_code == 400


def test_short_password_returns_400(client, db):
    res = client.post(
        "/api/v1/auth/register/open/",
        {"username": "shortpwuser", "password": "abc"},
        format="json",
    )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# School Student Registration
# ---------------------------------------------------------------------------


def test_school_student_registration_with_valid_code(client, invite_code, classroom):
    res = client.post(
        "/api/v1/auth/register/school/",
        {
            "username": "newschool_student",
            "password": "strongpass123",
            "email": "student@school.com",
            "first_name": "Test",
            "last_name": "Student",
            "join_code": "ABC123",
        },
        format="json",
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["role"] == "student"
    assert "access" in data


def test_school_student_registration_enrolls_in_classroom(client, invite_code, classroom):
    from openshiksha.apps.core.models import User

    res = client.post(
        "/api/v1/auth/register/school/",
        {"username": "enrolled_student", "password": "strongpass123", "join_code": "ABC123"},
        format="json",
    )
    assert res.status_code == 201
    user = User.objects.get(username="enrolled_student")
    assert classroom.students.filter(pk=user.pk).exists()


def test_registration_auto_enrolls_student_in_subject_rooms(client, invite_code, subject_room):
    from openshiksha.apps.core.models import User

    res = client.post(
        "/api/v1/auth/register/school/",
        {"username": "subroom_student", "password": "strongpass123", "join_code": "ABC123"},
        format="json",
    )
    assert res.status_code == 201
    user = User.objects.get(username="subroom_student")
    assert subject_room.students.filter(pk=user.pk).exists()


def test_school_student_registration_with_invalid_code_returns_400(client, db):
    res = client.post(
        "/api/v1/auth/register/school/",
        {"username": "bad_code_student", "password": "strongpass123", "join_code": "XXXXXX"},
        format="json",
    )
    assert res.status_code == 400


def test_inactive_code_returns_400(client, invite_code):
    invite_code.is_active = False
    invite_code.save()
    res = client.post(
        "/api/v1/auth/register/school/",
        {"username": "inactive_code_student", "password": "strongpass123", "join_code": "ABC123"},
        format="json",
    )
    assert res.status_code == 400


def test_school_registration_sets_correct_school(client, invite_code, classroom):
    from openshiksha.apps.core.models import User

    res = client.post(
        "/api/v1/auth/register/school/",
        {"username": "school_check_student", "password": "strongpass123", "join_code": "ABC123"},
        format="json",
    )
    assert res.status_code == 201
    user = User.objects.get(username="school_check_student")
    assert user.school == classroom.school
