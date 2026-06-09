"""
AIV-3a: read-only edit-safety flags on ProblemSet + Question serializers.

These flags exist purely to drive the teacher edit UX (AIV-3b banner) — they
do NOT gate writes. Integrity is already guaranteed by AIV-1/2 snapshots.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from django.utils import timezone
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
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="S", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Math")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="t", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="s", password="pw", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter, teacher):
    q = Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        created_by=teacher,
    )
    QuestionSubpart.objects.create(question=q, index=0, correct_answer={"answer": 1})
    return q


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question, teacher):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Set",
        number=1,
        created_by=teacher,
    )
    ps.questions.add(question)
    return ps


@pytest.fixture
def teacher_api(teacher):
    c = APIClient()
    c.force_authenticate(user=teacher)
    return c


class TestProblemSetEditSafety:
    def test_unused_set_has_zero_assigned_count(self, teacher_api, problem_set):
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/")
        assert resp.status_code == 200
        assert resp.data["assigned_count"] == 0
        assert resp.data["has_graded_submissions"] is False

    def test_assigned_count_reflects_number_of_assignments(self, teacher_api, problem_set, subject_room, teacher):
        for _ in range(2):
            Assignment.objects.create(
                problem_set=problem_set,
                subject_room=subject_room,
                assigned_by=teacher,
                due_at=timezone.now() + timedelta(days=3),
                number=Assignment.objects.filter(problem_set=problem_set).count() + 1,
            )
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/")
        assert resp.data["assigned_count"] == 2
        assert resp.data["has_graded_submissions"] is False

    def test_has_graded_submissions_true_when_any_graded_submission_exists(
        self, teacher_api, problem_set, subject_room, teacher, student
    ):
        a = Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
        )
        # Ungraded submission alone ⇒ flag stays false.
        Submission.objects.create(assignment=a, student=student, score=None)
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/")
        assert resp.data["has_graded_submissions"] is False

        # Grade the submission ⇒ flag flips true.
        Submission.objects.filter(assignment=a, student=student).update(score=0.8)
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/")
        assert resp.data["has_graded_submissions"] is True


class TestQuestionEditSafety:
    def test_unused_question_has_zero_assigned_count(self, teacher_api, question):
        resp = teacher_api.get(f"/api/v1/questions/{question.pk}/")
        assert resp.status_code == 200
        assert resp.data["assigned_count"] == 0
        assert resp.data["has_graded_submissions"] is False

    def test_question_used_via_problem_set_assignment(self, teacher_api, question, problem_set, subject_room, teacher):
        Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
        )
        resp = teacher_api.get(f"/api/v1/questions/{question.pk}/")
        assert resp.data["assigned_count"] == 1
        assert resp.data["has_graded_submissions"] is False
