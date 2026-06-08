"""
TW-3a: assignment close/reopen lifecycle.

Covers:
- POST /api/assignments/{id}/close/ sets closed_at + flips serialized status
- POST /api/assignments/{id}/reopen/ clears closed_at
- Submission write (create/update) rejected when assignment is closed
- Non-owner teacher cannot close another teacher's assignment
- Students and other roles get 403 on close/reopen
"""

from datetime import timedelta

import pytest

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Lifecycle School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=8)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="lc_teacher", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def other_teacher(db, school):
    return User.objects.create_user(username="lc_other_teacher", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="lc_student", password="pw", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def problem_set(db, school, standard, subject, chapter):
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Algebra #1",
        number=1,
    )
    ps.questions.add(q)
    return ps


@pytest.fixture
def assignment(db, subject_room, problem_set, teacher):
    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=3),
    )


class TestCloseReopen:
    def test_teacher_can_close_own_assignment(self, api_client, teacher, assignment):
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-close", args=[assignment.pk])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed_at"] is not None
        assert response.data["status"] == "closed"
        assignment.refresh_from_db()
        assert assignment.closed_at is not None

    def test_close_is_idempotent(self, api_client, teacher, assignment):
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-close", args=[assignment.pk])
        first = api_client.post(url)
        first_closed_at = first.data["closed_at"]
        second = api_client.post(url)
        assert second.status_code == status.HTTP_200_OK
        # closed_at should NOT advance on a repeated close
        assert second.data["closed_at"] == first_closed_at

    def test_teacher_can_reopen_own_assignment(self, api_client, teacher, assignment):
        assignment.closed_at = timezone.now()
        assignment.save(update_fields=["closed_at"])
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-reopen", args=[assignment.pk])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed_at"] is None
        assert response.data["status"] in ("active", "overdue")

    def test_other_teacher_cannot_close(self, api_client, other_teacher, assignment):
        api_client.force_authenticate(user=other_teacher)
        url = reverse("assignment-close", args=[assignment.pk])
        response = api_client.post(url)
        # The viewset filters queryset by assigned_by=user, so get_object 404s
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_cannot_close(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-close", args=[assignment.pk])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_status_reflects_overdue_when_past_due(self, api_client, teacher, assignment):
        assignment.due_at = timezone.now() - timedelta(days=1)
        assignment.save(update_fields=["due_at"])
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-detail", args=[assignment.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "overdue"


class TestSubmissionGuards:
    def test_student_cannot_create_submission_for_closed_assignment(self, api_client, student, assignment):
        assignment.closed_at = timezone.now()
        assignment.save(update_fields=["closed_at"])
        api_client.force_authenticate(user=student)
        url = reverse("submission-list")
        response = api_client.post(
            url,
            {"assignment": assignment.pk, "answers": {}, "completion": 0.0},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # error mentions closed
        assert "closed" in str(response.data).lower()

    def test_student_cannot_patch_submission_when_assignment_closed(self, api_client, student, assignment):
        # First create a submission while still open
        api_client.force_authenticate(user=student)
        list_url = reverse("submission-list")
        create = api_client.post(
            list_url,
            {"assignment": assignment.pk, "answers": {}, "completion": 0.0},
            format="json",
        )
        assert create.status_code == status.HTTP_201_CREATED
        sub_id = create.data["id"]
        # Now close the assignment
        assignment.closed_at = timezone.now()
        assignment.save(update_fields=["closed_at"])
        # Patch should be rejected
        detail_url = reverse("submission-detail", args=[sub_id])
        patch = api_client.patch(detail_url, {"completion": 0.5}, format="json")
        assert patch.status_code == status.HTTP_400_BAD_REQUEST

    def test_student_can_still_read_closed_assignment(self, api_client, student, assignment):
        """Closing blocks WRITES only — students must still see the assignment
        labelled "closed" rather than have it vanish."""
        assignment.closed_at = timezone.now()
        assignment.save(update_fields=["closed_at"])
        api_client.force_authenticate(user=student)
        url = reverse("assignment-detail", args=[assignment.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "closed"
