"""
Tests for ClassroomInviteCode model and classroom_code API action.
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

    return School.objects.create(name="Invite Test School", board=board)


@pytest.fixture
def school2(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Other School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=9, description="Grade 9")


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="inv_teacher", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def teacher2(db, school2):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="inv_teacher2", password="pass", role=UserRole.TEACHER, school=school2)


@pytest.fixture
def classroom(db, school, standard, teacher):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(
        school=school, standard=standard, division="B", class_teacher=teacher, academic_year="2024-25"
    )


@pytest.fixture
def classroom2(db, school2, standard, teacher2):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(
        school=school2, standard=standard, division="C", class_teacher=teacher2, academic_year="2024-25"
    )


@pytest.fixture
def authed_teacher_client(teacher):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(teacher)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def authed_teacher2_client(teacher2):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(teacher2)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


def test_generate_code_is_unique(db):
    from openshiksha.apps.core.models import ClassroomInviteCode

    codes = {ClassroomInviteCode.generate_code() for _ in range(20)}
    assert len(codes) == 20  # very unlikely to collide with 6-char codes


def test_code_length_is_six(db):
    from openshiksha.apps.core.models import ClassroomInviteCode

    code = ClassroomInviteCode.generate_code()
    assert len(code) == 6


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


def test_teacher_can_generate_code_for_own_classroom(authed_teacher_client, classroom):
    res = authed_teacher_client.post(
        "/api/v1/users/me/classroom-code/",
        {"classroom_id": classroom.id},
        format="json",
    )
    assert res.status_code == 201
    data = res.json()
    assert len(data["code"]) == 6
    assert data["classroom_id"] == classroom.id
    assert data["is_active"] is True


def test_teacher_cannot_generate_code_for_other_classroom(authed_teacher_client, classroom2):
    res = authed_teacher_client.post(
        "/api/v1/users/me/classroom-code/",
        {"classroom_id": classroom2.id},
        format="json",
    )
    assert res.status_code == 404


def test_regenerate_deactivates_old_code(authed_teacher_client, classroom, teacher):
    from openshiksha.apps.core.models import ClassroomInviteCode

    old = ClassroomInviteCode.objects.create(classroom=classroom, code="OLD123", created_by=teacher, is_active=True)
    authed_teacher_client.post(
        "/api/v1/users/me/classroom-code/",
        {"classroom_id": classroom.id},
        format="json",
    )
    old.refresh_from_db()
    assert old.is_active is False


def test_teacher_can_list_active_codes(authed_teacher_client, classroom, teacher):
    from openshiksha.apps.core.models import ClassroomInviteCode

    ClassroomInviteCode.objects.create(classroom=classroom, code="LIST01", created_by=teacher, is_active=True)
    res = authed_teacher_client.get("/api/v1/users/me/classroom-code/")
    assert res.status_code == 200
    codes = res.json()
    assert any(c["code"] == "LIST01" for c in codes)


def test_non_teacher_cannot_access_classroom_code(db, school, board, standard):
    from rest_framework_simplejwt.tokens import RefreshToken

    from openshiksha.apps.core.models import User, UserRole

    student = User.objects.create_user(username="notateacher", password="pass", role=UserRole.STUDENT, school=school)
    client = APIClient()
    refresh = RefreshToken.for_user(student)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    res = client.get("/api/v1/users/me/classroom-code/")
    assert res.status_code == 403
