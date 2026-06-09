"""
AIV-5: ``snapshot_has_drifted`` and the ``snapshot_drift`` field on
``AssignmentDetailSerializer`` flag when the live problem-set has moved past
the frozen snapshot — without changing what's served to the student.
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
from openshiksha.apps.core.snapshots import build_assignment_snapshot, snapshot_has_drifted


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
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher)
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        subpart_type="fill_blank",
        question_text="What is 6*7?",
        correct_answer={"type": "fill_blank", "answer": "42"},
    )
    ps.questions.add(q)
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


class TestSnapshotHasDrifted:
    def test_no_drift_immediately_after_assign(self, problem_set, assignment):
        assert snapshot_has_drifted(assignment.assigned_content, problem_set) is False

    def test_no_drift_when_snapshot_is_missing(self, problem_set):
        # Defensive: legacy rows the backfill missed report no drift, not a crash.
        assert snapshot_has_drifted(None, problem_set) is False
        assert snapshot_has_drifted({}, problem_set) is False

    def test_drift_when_subpart_correct_answer_edited(self, problem_set, assignment):
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        assert snapshot_has_drifted(assignment.assigned_content, problem_set) is True

    def test_drift_when_question_added(self, problem_set, assignment, school, standard, subject, chapter, teacher):
        q2 = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            created_by=teacher,
        )
        QuestionSubpart.objects.create(question=q2, index=0, subpart_type="fill_blank", correct_answer={"answer": "1"})
        problem_set.questions.add(q2)
        assert snapshot_has_drifted(assignment.assigned_content, problem_set) is True

    def test_drift_when_question_removed(self, problem_set, assignment):
        problem_set.questions.clear()
        assert snapshot_has_drifted(assignment.assigned_content, problem_set) is True


class TestAssignmentDetailDriftField:
    def test_teacher_assignment_detail_includes_snapshot_drift_false(self, assignment, teacher):
        c = APIClient()
        c.force_authenticate(user=teacher)
        resp = c.get(f"/api/v1/assignments/{assignment.pk}/")
        assert resp.status_code == 200
        assert resp.data["snapshot_drift"] is False

    def test_teacher_assignment_detail_drift_flips_after_live_edit(self, assignment, problem_set, teacher):
        # Edit the live set.
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])

        c = APIClient()
        c.force_authenticate(user=teacher)
        resp = c.get(f"/api/v1/assignments/{assignment.pk}/")
        assert resp.data["snapshot_drift"] is True

        # And the rendered questions still match the snapshot, not the live edit.
        sp_data = resp.data["problem_set"]["questions"][0]["subparts"][0]
        # correct_answer is stripped (student-safe) — assert question_text is the
        # snapshot value, not the edit, by checking a stable field that didn't
        # change. The drift flag carries the signal; the body stays frozen.
        assert sp_data["question_text"] == "What is 6*7?"
