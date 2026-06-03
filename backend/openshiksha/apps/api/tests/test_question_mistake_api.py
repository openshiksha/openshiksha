"""
Tests for QuestionMistakeViewSet.

Covers:
- Students are denied (403)
- Teachers only see their own subject rooms
- Cross-teacher isolation (teacher B cannot see teacher A's data)
- Results ordered by regression descending
"""

import pytest

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    ClassRoom,
    Question,
    QuestionSubpart,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import SubjectRoomQuestionMistake

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE-QM")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="QM School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Science-QM")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Motion", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="B", academic_year="2025-26")


@pytest.fixture
def classroom_b(db, school, standard):
    """A second classroom so teacher_b's subject room doesn't hit the unique constraint."""
    return ClassRoom.objects.create(school=school, standard=standard, division="C", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_qm", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def teacher_b(db, school):
    return User.objects.create_user(username="teacher_qm_b", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_qm", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def subject_room_b(db, classroom_b, subject, teacher_b, student):
    """A second subject room owned by teacher_b (different classroom to avoid unique constraint)."""
    room = SubjectRoom.objects.create(classroom=classroom_b, subject=subject, teacher=teacher_b)
    room.students.add(student)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter):
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)
    QuestionSubpart.objects.create(question=q, index=0, question_text="What is velocity?")
    return q


@pytest.fixture
def question2(db, school, standard, subject, chapter):
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)
    QuestionSubpart.objects.create(question=q, index=0, question_text="Define acceleration.")
    return q


@pytest.fixture
def mistake_high(db, subject_room, question):
    """High-regression mistake (regression=5.0)."""
    return SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question, regression=5.0)


@pytest.fixture
def mistake_low(db, subject_room, question2):
    """Low-regression mistake (regression=1.5)."""
    return SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question2, regression=1.5)


@pytest.fixture
def mistake_room_b(db, subject_room_b, question):
    """A mistake in teacher_b's room."""
    return SubjectRoomQuestionMistake.objects.create(subject_room=subject_room_b, question=question, regression=3.0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStudentDenied:
    def test_student_gets_403(self, api_client, student, subject_room, mistake_high):
        api_client.force_authenticate(user=student)
        url = reverse("question-mistake-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTeacherOwnership:
    def test_teacher_sees_own_rooms_only(self, api_client, teacher, subject_room, mistake_high, mistake_low):
        api_client.force_authenticate(user=teacher)
        url = reverse("question-mistake-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert mistake_high.id in ids
        assert mistake_low.id in ids

    def test_subject_room_filter_narrows_results(self, api_client, teacher, subject_room, mistake_high, mistake_low):
        api_client.force_authenticate(user=teacher)
        url = reverse("question-mistake-list")
        response = api_client.get(url, {"subject_room": subject_room.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


class TestCrossTeacherIsolation:
    def test_cross_teacher_isolation(
        self,
        api_client,
        teacher,
        teacher_b,
        subject_room,
        subject_room_b,
        mistake_high,
        mistake_room_b,
    ):
        # teacher_b should NOT see teacher's room mistakes
        api_client.force_authenticate(user=teacher_b)
        url = reverse("question-mistake-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert mistake_room_b.id in ids
        assert mistake_high.id not in ids


class TestOrdering:
    def test_results_ordered_by_regression_desc(self, api_client, teacher, subject_room, mistake_high, mistake_low):
        api_client.force_authenticate(user=teacher)
        url = reverse("question-mistake-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        regressions = [r["regression"] for r in response.data["results"]]
        assert regressions == sorted(regressions, reverse=True)
