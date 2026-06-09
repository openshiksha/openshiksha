"""
AIV-2b: the student assignment-detail endpoint serves the frozen snapshot,
not the live ProblemSet/Question/QuestionSubpart.

Editing the live set/question/subpart after the assignment was given MUST NOT
change what the student sees. The response shape is identical to the live
path; only the data source moves.
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
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        subpart_type="fill_blank",
        question_text="Original prompt",
        correct_answer={"type": "fill_blank", "answer": "42"},
    )
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
def assignment(db, problem_set, subject_room, teacher):
    return Assignment.objects.create(
        problem_set=problem_set,
        subject_room=subject_room,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
        assigned_content=build_assignment_snapshot(problem_set),
    )


@pytest.fixture
def api(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


class TestStudentSeesSnapshot:
    def test_student_sees_snapshot_prompt_not_live_edit(self, api, assignment, question):
        # Teacher edits live prompt AFTER assigning.
        sp = question.subparts.first()
        sp.question_text = "Edited prompt"
        sp.save(update_fields=["question_text"])

        resp = api.get(f"/api/v1/assignments/{assignment.pk}/")
        assert resp.status_code == 200
        questions = resp.data["problem_set"]["questions"]
        assert len(questions) == 1
        subparts = questions[0]["subparts"]
        assert subparts[0]["question_text"] == "Original prompt"

    def test_student_response_does_not_leak_correct_answer(self, api, assignment):
        resp = api.get(f"/api/v1/assignments/{assignment.pk}/")
        sp = resp.data["problem_set"]["questions"][0]["subparts"][0]
        assert "correct_answer" not in sp

    def test_student_response_shape_includes_widget_fields(self, api, assignment):
        resp = api.get(f"/api/v1/assignments/{assignment.pk}/")
        sp = resp.data["problem_set"]["questions"][0]["subparts"][0]
        # Shape parity with the live path — widget keys are always present.
        for key in ("widget_kind", "widget_config", "interactive_html", "is_interactive"):
            assert key in sp

    def test_student_sees_snapshot_after_question_removed_from_live_set(self, api, assignment, problem_set):
        # Teacher removes the question from the live set after assigning.
        problem_set.questions.clear()

        resp = api.get(f"/api/v1/assignments/{assignment.pk}/")
        assert resp.status_code == 200
        # The snapshot still has the question — student doesn't suddenly see an empty set.
        assert len(resp.data["problem_set"]["questions"]) == 1
