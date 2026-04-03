"""
API tests for:
- Assignment serializer analytics fields (submission_count, student_count)
- StudentProficiencyViewSet (student-only, own records)
- QuestionViewSet write operations (teacher-only)
- SubjectViewSet / ChapterViewSet (read-only for authenticated users)
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
from openshiksha.apps.edge.models import StudentProficiency

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_analytics", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_analytics", password="pass", role=UserRole.STUDENT, school=school)


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
        title="Algebra Practice #1",
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


@pytest.fixture
def question_tag(db):
    from openshiksha.apps.core.models import QuestionTag

    return QuestionTag.objects.create(name="Quadratic Equations", tag_type="concept")


# ---------------------------------------------------------------------------
# Assignment analytics fields
# ---------------------------------------------------------------------------


class TestAssignmentAnalyticsFields:
    def test_teacher_sees_submission_count_and_student_count(self, api_client, teacher, student, assignment):
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.data["results"][0]
        assert "submission_count" in result
        assert "student_count" in result
        # No submissions yet
        assert result["submission_count"] == 0
        # subject_room has 1 student enrolled
        assert result["student_count"] == 1

    def test_submission_count_increments_when_student_submits(self, api_client, teacher, student, assignment):
        Submission.objects.create(assignment=assignment, student=student)
        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-list")
        response = api_client.get(url)
        result = response.data["results"][0]
        assert result["submission_count"] == 1

    def test_student_also_receives_analytics_fields(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.data["results"][0]
        assert "submission_count" in result
        assert "student_count" in result


# ---------------------------------------------------------------------------
# StudentProficiencyViewSet
# ---------------------------------------------------------------------------


class TestStudentProficiencyViewSet:
    def test_unauthenticated_cannot_access(self, api_client):
        url = reverse("proficiency-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_teacher_cannot_access_proficiency(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("proficiency-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_sees_empty_list_with_no_proficiency(self, api_client, student):
        api_client.force_authenticate(user=student)
        url = reverse("proficiency-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_student_sees_own_proficiency_records(self, api_client, student, subject_room, question_tag):
        StudentProficiency.objects.create(
            student=student,
            question_tag=question_tag,
            subject_room=subject_room,
            score=0.75,
            rate=0.8,
            tick_count=5,
        )
        api_client.force_authenticate(user=student)
        url = reverse("proficiency-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        record = response.data["results"][0]
        assert record["tag_name"] == "Quadratic Equations"
        assert record["subject_name"] == "Mathematics"
        assert float(record["score"]) == pytest.approx(0.75)
        assert record["tick_count"] == 5

    def test_student_cannot_see_other_students_proficiency(self, api_client, school, subject_room, question_tag, db):
        other_student = User.objects.create_user(
            username="other_student_prof", password="pass", role=UserRole.STUDENT, school=school
        )
        StudentProficiency.objects.create(
            student=other_student,
            question_tag=question_tag,
            subject_room=subject_room,
            score=0.5,
            tick_count=3,
        )
        my_student = User.objects.create_user(
            username="my_student_prof", password="pass", role=UserRole.STUDENT, school=school
        )
        api_client.force_authenticate(user=my_student)
        url = reverse("proficiency-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0


# ---------------------------------------------------------------------------
# QuestionViewSet write operations
# ---------------------------------------------------------------------------


class TestQuestionViewSetWrite:
    def test_teacher_can_create_question_with_subparts(self, api_client, teacher, school, standard, subject, chapter):
        api_client.force_authenticate(user=teacher)
        url = reverse("question-list")
        data = {
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_type": "mcq",
            "difficulty": 2,
            "subparts": [
                {
                    "index": 0,
                    "question_text": r"Solve $x^2 - 4 = 0$",
                    "options": [{"key": "A", "text": "x = ±2"}, {"key": "B", "text": "x = 4"}],
                    "correct_answer": {"type": "mcq", "answer": "A"},
                }
            ],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Question.objects.filter(chapter=chapter).count() == 1
        question = Question.objects.get(chapter=chapter)
        assert question.subparts.count() == 1
        assert question.created_by == teacher

    def test_student_cannot_create_question(self, api_client, student, standard, subject, chapter):
        api_client.force_authenticate(user=student)
        url = reverse("question-list")
        data = {
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_type": "mcq",
            "difficulty": 1,
            "subparts": [{"index": 0, "question_text": "Test", "correct_answer": {}}],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_question_requires_at_least_one_subpart(self, api_client, teacher, standard, subject, chapter):
        api_client.force_authenticate(user=teacher)
        url = reverse("question-list")
        data = {
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_type": "mcq",
            "difficulty": 1,
            "subparts": [],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_read_questions(self, api_client):
        url = reverse("question-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# SubjectViewSet and ChapterViewSet
# ---------------------------------------------------------------------------


class TestSubjectChapterViewSets:
    def test_authenticated_user_can_list_subjects(self, api_client, student, subject):
        api_client.force_authenticate(user=student)
        url = reverse("subject-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_authenticated_user_can_list_chapters(self, api_client, student, chapter):
        api_client.force_authenticate(user=student)
        url = reverse("chapter-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_chapters_filterable_by_subject(self, api_client, teacher, subject, chapter):
        api_client.force_authenticate(user=teacher)
        url = reverse("chapter-list")
        response = api_client.get(url, {"subject": subject.pk})
        assert response.status_code == status.HTTP_200_OK
        assert all(r["subject"] == subject.pk for r in response.data["results"])

    def test_unauthenticated_cannot_list_subjects(self, api_client):
        url = reverse("subject-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
