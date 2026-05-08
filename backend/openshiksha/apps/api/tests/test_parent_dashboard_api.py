"""
Tests for parent dashboard API endpoints.

Covers:
- GET /api/users/me/children/ — authenticated parent gets their linked children
- GET /api/proficiency/?student=<id> — parent reads child proficiency (ownership enforced)
- Non-parent roles cannot access the children endpoint
"""

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    ClassRoom,
    QuestionTag,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import StudentProficiency


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=5)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Fractions", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A")


@pytest.fixture
def teacher_user(db, school):
    return User.objects.create_user(
        username="teacher1",
        password="pass",
        role=UserRole.TEACHER,
        school=school,
    )


@pytest.fixture
def student_user(db, school):
    return User.objects.create_user(
        username="student1",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
    )


@pytest.fixture
def other_student_user(db, school):
    return User.objects.create_user(
        username="student2",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
    )


@pytest.fixture
def parent_user(db, student_user):
    parent = User.objects.create_user(
        username="parent1",
        password="pass",
        role=UserRole.PARENT,
    )
    parent.children.add(student_user)
    return parent


@pytest.fixture
def subject_room(db, classroom, subject, teacher_user, student_user):
    room = SubjectRoom.objects.create(
        classroom=classroom,
        subject=subject,
        teacher=teacher_user,
    )
    room.students.add(student_user)
    return room


@pytest.fixture
def question_tag(db):
    return QuestionTag.objects.create(name="Fractions Basics", tag_type="concept")


@pytest.fixture
def proficiency_record(db, student_user, subject_room, question_tag):
    return StudentProficiency.objects.create(
        student=student_user,
        subject_room=subject_room,
        question_tag=question_tag,
        score=0.75,
        rate=0.80,
        percentile=0.65,
        tick_count=10,
    )


# ---------------------------------------------------------------------------
# GET /api/users/me/children/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_parent_gets_children_list(api_client, parent_user, student_user):
    """Parent can retrieve their linked children via GET /api/users/me/children/."""
    api_client.force_authenticate(user=parent_user)
    response = api_client.get("/api/v1/users/me/children/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == student_user.id
    assert data[0]["username"] == student_user.username


@pytest.mark.django_db
def test_non_parent_cannot_access_children_endpoint(api_client, student_user, teacher_user):
    """Students and teachers receive 403 when accessing the children endpoint."""
    for user in (student_user, teacher_user):
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/users/me/children/")
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), f"Expected 403 for role={user.role}, got {response.status_code}"


@pytest.mark.django_db
def test_unauthenticated_cannot_access_children_endpoint(api_client):
    """Unauthenticated requests to the children endpoint return 401."""
    response = api_client.get("/api/v1/users/me/children/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# GET /api/proficiency/?student=<id>
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_parent_can_read_own_childs_proficiency(api_client, parent_user, student_user, proficiency_record):
    """Parent reads proficiency for their own child."""
    api_client.force_authenticate(user=parent_user)
    response = api_client.get(f"/api/v1/proficiency/?student={student_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    results = data.get("results", data)
    assert len(results) >= 1
    ids = [r["id"] for r in results]
    assert proficiency_record.id in ids


@pytest.mark.django_db
def test_parent_cannot_see_other_students_proficiency(
    api_client, parent_user, other_student_user, subject_room, question_tag
):
    """Parent cannot read proficiency for a student not in their children list."""
    # Create a proficiency record for other_student_user (not parent's child)
    tag2 = QuestionTag.objects.create(name="Other Tag", tag_type="concept")
    StudentProficiency.objects.create(
        student=other_student_user,
        subject_room=subject_room,
        question_tag=tag2,
        score=0.5,
        rate=0.5,
        percentile=0.5,
        tick_count=5,
    )
    api_client.force_authenticate(user=parent_user)
    response = api_client.get(f"/api/v1/proficiency/?student={other_student_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    results = data.get("results", data)
    assert len(results) == 0, "Parent should not see proficiency of unlinked students"


@pytest.mark.django_db
def test_parent_with_no_student_param_gets_empty_proficiency(api_client, parent_user):
    """Parent without ?student= param gets empty proficiency (not their own records)."""
    api_client.force_authenticate(user=parent_user)
    response = api_client.get("/api/v1/proficiency/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    results = data.get("results", data)
    assert len(results) == 0
