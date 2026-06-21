"""
TW-2 / AIV-4: editing the live problem set's question list must NOT change any
existing assignment's snapshot. This is the property that makes the editable
preview safe to ship.

Mirrors the AIV-1 byte-identical guarantee at the API surface — through the
``add-question`` and ``remove-question`` endpoints that the editable preview
calls — so a regression in either path fails the test.
"""

from __future__ import annotations

import copy
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
    User,
    UserRole,
)
from openshiksha.apps.core.snapshots import build_assignment_snapshot


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
def other_teacher(db, school):
    return User.objects.create_user(username="t2", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="s", password="pw", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


def _make_question(school, standard, subject, chapter, teacher, *, text):
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher)
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        subpart_type="fill_blank",
        question_text=text,
        correct_answer={"type": "fill_blank", "answer": "42"},
    )
    return q


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, teacher):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Set",
        number=1,
        created_by=teacher,
    )
    q1 = _make_question(school, standard, subject, chapter, teacher, text="Q1")
    q2 = _make_question(school, standard, subject, chapter, teacher, text="Q2")
    ps.questions.add(q1, q2)
    return ps


@pytest.fixture
def assignment(db, problem_set, subject_room, teacher):
    return Assignment.objects.create(
        problem_set=problem_set,
        subject_room=subject_room,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=3),
        assigned_content=build_assignment_snapshot(problem_set),
    )


@pytest.fixture
def teacher_api(teacher):
    c = APIClient()
    c.force_authenticate(user=teacher)
    return c


class TestProblemSetEditableLiveAPIs:
    def test_remove_question_does_not_change_existing_assignment_snapshot(self, teacher_api, problem_set, assignment):
        """AIV-4 / TW-2 golden test: removing a question from the live set must
        not change any pre-existing assignment's snapshot. AIV-1 stored the
        snapshot at assign time; AIV-2 reads from it. This proves the cycle."""
        original_snapshot = copy.deepcopy(assignment.assigned_content)
        live_question = problem_set.questions.first()

        resp = teacher_api.post(
            f"/api/v1/problem-sets/{problem_set.pk}/remove-question/",
            {"question_id": live_question.pk},
            format="json",
        )
        assert resp.status_code == 200

        # Live set lost the question.
        problem_set.refresh_from_db()
        assert not problem_set.questions.filter(pk=live_question.pk).exists()

        # But the existing assignment's snapshot is byte-identical.
        assignment.refresh_from_db()
        assert assignment.assigned_content == original_snapshot

    def test_add_question_does_not_change_existing_assignment_snapshot(
        self, teacher_api, problem_set, assignment, school, standard, subject, chapter, teacher
    ):
        original_snapshot = copy.deepcopy(assignment.assigned_content)
        new_question = _make_question(school, standard, subject, chapter, teacher, text="Q3-new")

        resp = teacher_api.post(
            f"/api/v1/problem-sets/{problem_set.pk}/add-question/",
            {"question_id": new_question.pk},
            format="json",
        )
        assert resp.status_code == 200

        # Live set gained the question.
        problem_set.refresh_from_db()
        assert problem_set.questions.filter(pk=new_question.pk).exists()

        # Existing assignment's snapshot is untouched.
        assignment.refresh_from_db()
        assert assignment.assigned_content == original_snapshot

    def test_remove_question_requires_creator(self, problem_set, other_teacher):
        c = APIClient()
        c.force_authenticate(user=other_teacher)
        live_question = problem_set.questions.first()
        resp = c.post(
            f"/api/v1/problem-sets/{problem_set.pk}/remove-question/",
            {"question_id": live_question.pk},
            format="json",
        )
        assert resp.status_code == 403

    def test_remove_question_requires_question_id(self, teacher_api, problem_set):
        resp = teacher_api.post(
            f"/api/v1/problem-sets/{problem_set.pk}/remove-question/",
            {},
            format="json",
        )
        assert resp.status_code == 400
