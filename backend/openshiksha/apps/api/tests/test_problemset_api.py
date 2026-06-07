"""
Tests for ProblemSet write API and submission student_name field.
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
    QuestionSubpart,
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
    return Subject.objects.create(name="Maths")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Quadratics", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(
        username="teacher_ps",
        password="pass",
        role=UserRole.TEACHER,
        school=school,
        first_name="Test",
        last_name="Teacher",
    )


@pytest.fixture
def student(db, school):
    return User.objects.create_user(
        username="student_ps",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        first_name="Arjun",
        last_name="Sharma",
    )


@pytest.fixture
def question(db, school, standard, subject, chapter, teacher):
    q = Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        created_by=teacher,
    )
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        question_text="Solve $x^2 - 4 = 0$",
        options=[
            {"key": "A", "text": "x=2"},
            {"key": "B", "text": "x=-2"},
            {"key": "C", "text": "x=0"},
            {"key": "D", "text": "x=4"},
        ],
        correct_answer={"type": "mcq", "answer": "A"},
    )
    return q


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question, teacher):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Existing PS",
        number=1,
        created_by=teacher,
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


class TestProblemSetCreate:
    def test_teacher_can_create_problem_set(self, api_client, teacher, standard, subject, chapter, question):
        api_client.force_authenticate(user=teacher)
        url = reverse("problemset-list")
        data = {
            "title": "New Practice Set",
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_ids": [question.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] is not None

    def test_created_problem_set_has_questions(self, api_client, teacher, standard, subject, chapter, question):
        api_client.force_authenticate(user=teacher)
        url = reverse("problemset-list")
        data = {
            "title": "Set With Questions",
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_ids": [question.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        ps = ProblemSet.objects.get(pk=response.data["id"])
        assert ps.questions.filter(pk=question.pk).exists()

    def test_student_cannot_create_problem_set(self, api_client, student, standard, subject, chapter, question):
        api_client.force_authenticate(user=student)
        url = reverse("problemset-list")
        data = {
            "title": "Student Attempt",
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_ids": [question.pk],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_requires_at_least_one_question(self, api_client, teacher, standard, subject, chapter):
        api_client.force_authenticate(user=teacher)
        url = reverse("problemset-list")
        data = {
            "title": "Empty Set",
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_ids": [],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_includes_newly_created(self, api_client, teacher, standard, subject, chapter, question, school):
        api_client.force_authenticate(user=teacher)
        url = reverse("problemset-list")
        data = {
            "title": "Brand New PS",
            "standard": standard.pk,
            "subject": subject.pk,
            "chapter": chapter.pk,
            "question_ids": [question.pk],
        }
        api_client.post(url, data, format="json")
        list_response = api_client.get(url)
        assert list_response.status_code == status.HTTP_200_OK
        titles = [ps["title"] for ps in list_response.data["results"]]
        assert "Brand New PS" in titles


class TestSubmissionStudentName:
    def test_submissions_endpoint_includes_student_name(self, api_client, teacher, student, assignment):
        # Create a submission
        sub = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={},
        )
        sub.submitted_at = timezone.now()
        sub.save(update_fields=["submitted_at"])

        api_client.force_authenticate(user=teacher)
        url = reverse("assignment-submissions", kwargs={"pk": assignment.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        submission_data = response.data[0]
        assert "student_name" in submission_data
        # Student has first_name="Arjun", last_name="Sharma"
        assert submission_data["student_name"] == "Arjun Sharma"

    def test_student_cannot_access_submissions_endpoint(self, api_client, student, assignment):
        api_client.force_authenticate(user=student)
        url = reverse("assignment-submissions", kwargs={"pk": assignment.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddQuestionToProblemSet:
    """Tests for POST /api/v1/problem-sets/<id>/add-question/"""

    @pytest.fixture
    def extra_question(self, db, school, standard, subject, chapter, teacher):
        q = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            created_by=teacher,
        )
        QuestionSubpart.objects.create(
            question=q,
            index=0,
            question_text="Another question?",
            options=[
                {"key": "A", "text": "Yes"},
                {"key": "B", "text": "No"},
            ],
            correct_answer={"type": "mcq", "answer": "A"},
        )
        return q

    def test_teacher_can_add_question(self, api_client, teacher, problem_set, extra_question):
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {"question_id": extra_question.pk}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert problem_set.questions.filter(pk=extra_question.pk).exists()

    def test_add_question_is_idempotent(self, api_client, teacher, problem_set, question):
        """Adding an already-present question does not raise an error."""
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {"question_id": question.pk}, format="json")
        assert response.status_code == status.HTTP_200_OK
        # Still exactly one such question
        assert problem_set.questions.filter(pk=question.pk).count() == 1

    def test_student_cannot_add_question(self, api_client, student, problem_set, extra_question):
        api_client.force_authenticate(user=student)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {"question_id": extra_question.pk}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_other_teacher_cannot_add_to_problem_set(self, api_client, school, problem_set, extra_question, board):
        other_teacher = User.objects.create_user(
            username="other_teacher",
            password="pass",
            role=UserRole.TEACHER,
            school=school,
        )
        api_client.force_authenticate(user=other_teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {"question_id": extra_question.pk}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_question_id_returns_400(self, api_client, teacher, problem_set):
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_question_returns_404(self, api_client, teacher, problem_set):
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/add-question/"
        response = api_client.post(url, {"question_id": 99999}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProblemSetStudentPreview:
    """Tests for GET /api/v1/problem-sets/<id>/preview/ (view-as-student)."""

    def test_teacher_can_preview_with_questions(self, api_client, teacher, problem_set, question):
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/preview/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == problem_set.pk
        assert len(response.data["questions"]) == 1
        assert response.data["questions"][0]["id"] == question.pk
        assert len(response.data["questions"][0]["subparts"]) == 1

    def test_preview_hides_correct_answer(self, api_client, teacher, problem_set):
        """The student serializer must never leak the correct answer."""
        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/problem-sets/{problem_set.pk}/preview/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        subpart = response.data["questions"][0]["subparts"][0]
        assert "correct_answer" not in subpart

    def test_student_cannot_preview(self, api_client, student, problem_set):
        api_client.force_authenticate(user=student)
        url = f"/api/v1/problem-sets/{problem_set.pk}/preview/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_preview_unknown_set_returns_404(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        response = api_client.get("/api/v1/problem-sets/99999/preview/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestClassroomCodeForSubjectTeacher:
    """The join code must work for a subject teacher who is *not* the homeroom
    ``class_teacher`` — the dashboard surfaces it per subject room."""

    def test_subject_teacher_can_generate_code(self, api_client, teacher, classroom, subject_room):
        # `teacher` runs `subject_room` in `classroom` but is NOT its class_teacher.
        assert classroom.class_teacher_id is None
        api_client.force_authenticate(user=teacher)
        url = "/api/v1/users/me/classroom-code/"
        response = api_client.post(url, {"classroom_id": classroom.pk}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["code"]
        assert response.data["classroom_id"] == classroom.pk

    def test_subject_teacher_sees_code_in_list(self, api_client, teacher, classroom, subject_room):
        api_client.force_authenticate(user=teacher)
        url = "/api/v1/users/me/classroom-code/"
        api_client.post(url, {"classroom_id": classroom.pk}, format="json")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(c["classroom_id"] == classroom.pk for c in response.data)

    def test_unrelated_teacher_cannot_generate_code(self, api_client, school, classroom):
        outsider = User.objects.create_user(
            username="outsider_teacher",
            password="pass",
            role=UserRole.TEACHER,
            school=school,
        )
        api_client.force_authenticate(user=outsider)
        url = "/api/v1/users/me/classroom-code/"
        response = api_client.post(url, {"classroom_id": classroom.pk}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
