"""
AIV-6: ``resync-preview``, ``resync``, and ``undo-resync`` actions on the
assignment endpoint. Re-sync is opt-in, previewable, and reversible — the
prior snapshot is archived in ``AssignmentSnapshotHistory`` so undo restores
it byte-for-byte.
"""

from __future__ import annotations

import copy
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Assignment,
    AssignmentSnapshotHistory,
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
from openshiksha.apps.core.snapshots import build_assignment_snapshot, diff_snapshots


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


@pytest.fixture
def teacher_api(teacher):
    c = APIClient()
    c.force_authenticate(user=teacher)
    return c


class TestDiffSnapshots:
    def test_no_diff_for_identical(self, problem_set, assignment):
        d = diff_snapshots(assignment.assigned_content, assignment.assigned_content)
        assert d == {"questions_added": [], "questions_removed": [], "answer_changes": [], "content_changes": []}

    def test_detects_answer_change(self, problem_set, assignment):
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        d = diff_snapshots(assignment.assigned_content, build_assignment_snapshot(problem_set))
        assert len(d["answer_changes"]) == 1
        assert d["answer_changes"][0]["before"] == {"type": "fill_blank", "answer": "42"}
        assert d["answer_changes"][0]["after"] == {"type": "fill_blank", "answer": "999"}

    def test_detects_content_change_without_answer_change(self, problem_set, assignment):
        sp = problem_set.questions.first().subparts.first()
        sp.question_text = "What is six times seven?"
        sp.save(update_fields=["question_text"])
        d = diff_snapshots(assignment.assigned_content, build_assignment_snapshot(problem_set))
        assert d["answer_changes"] == []
        assert len(d["content_changes"]) == 1

    def test_detects_added_question(self, problem_set, assignment, school, standard, subject, chapter, teacher):
        q2 = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            created_by=teacher,
        )
        QuestionSubpart.objects.create(question=q2, index=0, subpart_type="fill_blank", correct_answer={"answer": "1"})
        problem_set.questions.add(q2)
        d = diff_snapshots(assignment.assigned_content, build_assignment_snapshot(problem_set))
        assert d["questions_added"] == [q2.pk]


class TestResyncPreview:
    def test_returns_empty_diff_when_no_drift(self, teacher_api, assignment):
        resp = teacher_api.get(f"/api/v1/assignments/{assignment.pk}/resync-preview/")
        assert resp.status_code == 200
        assert resp.data["has_drift"] is False
        assert resp.data["diff"]["answer_changes"] == []
        assert resp.data["affected"]["regrade_on_apply"] == 0

    def test_reports_regrade_count_when_answers_changed(self, teacher_api, assignment, problem_set, student):
        # One graded submission exists.
        Submission.objects.create(
            assignment=assignment,
            student=student,
            score=1.0,
            completion=1.0,
            submitted_at=timezone.now(),
        )
        # Live edit.
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])

        resp = teacher_api.get(f"/api/v1/assignments/{assignment.pk}/resync-preview/")
        assert resp.status_code == 200
        assert resp.data["has_drift"] is True
        assert resp.data["affected"]["regrade_on_apply"] == 1

    def test_is_read_only(self, teacher_api, problem_set, assignment):
        # Live edit then preview — assigned_content must not change.
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        original = copy.deepcopy(assignment.assigned_content)

        teacher_api.get(f"/api/v1/assignments/{assignment.pk}/resync-preview/")
        assignment.refresh_from_db()
        assert assignment.assigned_content == original


class TestResyncApply:
    @patch("openshiksha.apps.core.tasks.grade_submission")
    def test_resync_archives_prior_snapshot_and_swaps(self, mock_grade, teacher_api, assignment, problem_set):
        mock_grade.delay = MagicMock()
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        original = copy.deepcopy(assignment.assigned_content)

        resp = teacher_api.post(f"/api/v1/assignments/{assignment.pk}/resync/")
        assert resp.status_code == 200

        assignment.refresh_from_db()
        # New snapshot has the new answer.
        new_sp = assignment.assigned_content["questions"][0]["subparts"][0]
        assert new_sp["correct_answer"] == {"type": "fill_blank", "answer": "999"}

        # Prior snapshot archived.
        history = AssignmentSnapshotHistory.objects.filter(assignment=assignment)
        assert history.count() == 1
        assert history.first().content == original

    @patch("openshiksha.apps.core.tasks.grade_submission")
    def test_resync_triggers_regrade_when_answers_changed(
        self, mock_grade, teacher_api, assignment, problem_set, student
    ):
        mock_grade.delay = MagicMock()
        sub = Submission.objects.create(
            assignment=assignment,
            student=student,
            score=1.0,
            completion=1.0,
            submitted_at=timezone.now(),
        )
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])

        # Submission.post_save signal also queues grade_submission — reset so the
        # assert isolates the resync-triggered re-grade.
        mock_grade.delay.reset_mock()
        resp = teacher_api.post(f"/api/v1/assignments/{assignment.pk}/resync/")
        assert resp.status_code == 200
        assert resp.data["regraded_submission_count"] == 1
        mock_grade.delay.assert_called_once_with(sub.pk)

    @patch("openshiksha.apps.core.tasks.grade_submission")
    def test_resync_skips_regrade_when_only_content_changed(
        self, mock_grade, teacher_api, assignment, problem_set, student
    ):
        mock_grade.delay = MagicMock()
        Submission.objects.create(
            assignment=assignment,
            student=student,
            score=1.0,
            completion=1.0,
            submitted_at=timezone.now(),
        )
        # Only cosmetic edit.
        sp = problem_set.questions.first().subparts.first()
        sp.question_text = "Different prompt"
        sp.save(update_fields=["question_text"])

        mock_grade.delay.reset_mock()
        resp = teacher_api.post(f"/api/v1/assignments/{assignment.pk}/resync/")
        assert resp.status_code == 200
        assert resp.data["regraded_submission_count"] == 0
        mock_grade.delay.assert_not_called()


class TestUndoResync:
    @patch("openshiksha.apps.core.tasks.grade_submission")
    def test_undo_restores_prior_snapshot_byte_for_byte(self, mock_grade, teacher_api, assignment, problem_set):
        mock_grade.delay = MagicMock()
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        original = copy.deepcopy(assignment.assigned_content)

        teacher_api.post(f"/api/v1/assignments/{assignment.pk}/resync/")
        resp = teacher_api.post(f"/api/v1/assignments/{assignment.pk}/undo-resync/")
        assert resp.status_code == 200

        assignment.refresh_from_db()
        assert assignment.assigned_content == original
        assert AssignmentSnapshotHistory.objects.filter(assignment=assignment).count() == 0

    def test_undo_returns_404_when_no_history(self, teacher_api, assignment):
        resp = teacher_api.post(f"/api/v1/assignments/{assignment.pk}/undo-resync/")
        assert resp.status_code == 404
