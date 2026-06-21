"""
API tests for Assignment and Submission endpoints.
Tests permission enforcement and core workflow.
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
    Submission,
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
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=10)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Kinematics", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="C", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_api", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_api", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def other_student(db, school):
    return User.objects.create_user(username="other_student_api", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter):
    return Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Kinematics Practice #1",
        number=1,
    )
    ps.questions.add(question)
    return ps


@pytest.fixture
def assignment(db, subject_room, problem_set, teacher):
    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
    )


class TestAssignmentPermissions:
    def test_unauthenticated_cannot_list(self, api_client):
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_student_can_list_assignments(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_teacher_can_list_assignments(self, api_client, teacher, assignment):
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_teacher_can_create_assignment(self, api_client, teacher, subject_room, problem_set):
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-list")
        data = {
            "subject_room": subject_room.pk,
            "problem_set_id": problem_set.pk,
            "due_at": (timezone.now() + timedelta(days=5)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_student_cannot_create_assignment(self, api_client, student, subject_room, problem_set):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-list")
        data = {
            "subject_room": subject_room.pk,
            "problem_set_id": problem_set.pk,
            "due_at": (timezone.now() + timedelta(days=5)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_sees_only_their_assignments(self, api_client, student, other_student, assignment):
        # other_student is not enrolled in the subject_room
        api_client.force_authenticate(user=other_student)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_enrolled_student_sees_assignment(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_assignment_list_includes_my_submission_for_students(self, api_client, student, assignment, db):
        """Regression for the StudentDashboard "due soon even though submitted"
        bug: the LIST endpoint must surface ``my_submission`` so the dashboard
        can group submitted rows into Completed instead of Due Soon. Used to
        be on the detail serializer only; promoted to the base serializer."""
        from django.utils import timezone

        from openshiksha.apps.core.models import Submission

        Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={},
            completion=1.0,
            submitted_at=timezone.now(),
        )
        api_client.force_authenticate(user=student)
        response = api_client.get(reverse("assignment-list"))
        assert response.status_code == status.HTTP_200_OK
        row = response.data["results"][0]
        assert "my_submission" in row
        assert row["my_submission"] is not None
        assert row["my_submission"]["submitted_at"] is not None

    def test_assignment_list_my_submission_is_null_when_unsubmitted(self, api_client, student, assignment):
        """Unsubmitted assignments must explicitly serialise ``my_submission: null``
        so the frontend filter doesn't have to infer "missing key" semantics."""
        api_client.force_authenticate(user=student)
        response = api_client.get(reverse("assignment-list"))
        assert response.status_code == status.HTTP_200_OK
        row = response.data["results"][0]
        assert row.get("my_submission") is None

    def test_assignment_list_my_submission_is_null_for_teachers(self, api_client, teacher, assignment):
        """``my_submission`` is a student concept — for teachers the field must
        return ``null`` rather than leaking the first matched submission."""
        api_client.force_authenticate(user=teacher)
        response = api_client.get(reverse("assignment-list"))
        assert response.status_code == status.HTTP_200_OK
        row = response.data["results"][0]
        assert row.get("my_submission") is None


class TestSubmissionWorkflow:
    def test_student_can_create_submission(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("submission-list")
        data = {
            "assignment": assignment.pk,
            "answers": {"1": 2},
            "completion": 0.5,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["student"] == student.pk

    def test_teacher_cannot_create_submission(self, api_client, teacher, assignment):
        api_client.force_authenticate(user=teacher)
        url = reverse("submission-list")
        data = {
            "assignment": assignment.pk,
            "answers": {"1": 2},
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_submit_twice(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("submission-list")
        data = {"assignment": assignment.pk, "answers": {}, "completion": 0.0}
        api_client.post(url, data, format="json")
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_student_can_update_submission(self, api_client, student, assignment):
        sub = Submission.objects.create(assignment=assignment, student=student, answers={"1": 1}, completion=0.5)
        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": sub.pk})
        response = api_client.patch(url, {"answers": {"1": 3}, "completion": 1.0}, format="json")
        assert response.status_code == status.HTTP_200_OK
        sub.refresh_from_db()
        assert sub.answers == {"1": 3}

    def test_student_sees_only_own_submission(self, api_client, student, other_student, assignment, db):
        Submission.objects.create(assignment=assignment, student=student)
        Submission.objects.create(assignment=assignment, student=other_student)
        api_client.force_authenticate(user=student)
        url = reverse("submission-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["student"] == student.pk
