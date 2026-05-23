"""
Tests for the remedial assignment auto-creation pipeline.

When a student scores below REMEDIAL_THRESHOLD (0.30) on a graded assignment,
_create_remedial_assignment should auto-create a new ProblemSet + Assignment
targeting only the questions they got wrong.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

# ---------------------------------------------------------------------------
# Shared fixtures (mirrors test_grading_tasks.py setup)
# ---------------------------------------------------------------------------


@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Remedial Test School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.create(name="Biology")


@pytest.fixture
def chapter(db, subject, standard):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.create(name="Photosynthesis", subject=subject, standard=standard, order=1)


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="remedial_teacher", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="remedial_student", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def classroom(db, school, standard):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    from openshiksha.apps.core.models import SubjectRoom

    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter):
    from openshiksha.apps.core.models import Question

    return Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type="mcq",
    )


@pytest.fixture
def subpart_a(db, question):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(question=question, index=0, correct_answer={"answer": 1})


@pytest.fixture
def subpart_b(db, question):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(question=question, index=1, correct_answer={"answer": 2})


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    from openshiksha.apps.core.models import ProblemSet

    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Photosynthesis PS1",
        number=1,
    )
    ps.questions.add(question)
    return ps


@pytest.fixture
def assignment(db, problem_set, subject_room, teacher):
    from openshiksha.apps.core.models import Assignment

    return Assignment.objects.create(
        problem_set=problem_set,
        subject_room=subject_room,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRemedialAssignmentCreation:
    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_remedial_created_when_score_below_threshold(
        self, mock_prof, mock_agg, db, assignment, student, subpart_a, subpart_b
    ):
        """When a student scores below 0.30, a remedial ProblemSet + Assignment is auto-created."""
        from openshiksha.apps.core.models import Assignment, ProblemSet, Submission
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        # All answers wrong → score = 0
        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={
                str(subpart_a.id): 99,  # wrong
                str(subpart_b.id): 99,  # wrong
            },
        )
        grade_submission(submission.pk)

        remedial_ps = ProblemSet.objects.filter(is_remedial=True, source_assignment=assignment).first()
        assert remedial_ps is not None, "Remedial ProblemSet should have been created"
        assert remedial_ps.title == f"Remedial: {assignment.problem_set.title}"

        remedial_assignment = Assignment.objects.filter(problem_set=remedial_ps).first()
        assert remedial_assignment is not None
        assert remedial_assignment.subject_room == assignment.subject_room

    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_remedial_not_created_when_score_above_threshold(
        self, mock_prof, mock_agg, db, assignment, student, subpart_a, subpart_b
    ):
        """When a student scores >= 0.30, no remedial is created."""
        from openshiksha.apps.core.models import ProblemSet, Submission
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        # Both answers correct → score = 1.0
        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={
                str(subpart_a.id): 1,  # correct
                str(subpart_b.id): 2,  # correct
            },
        )
        grade_submission(submission.pk)

        assert not ProblemSet.objects.filter(is_remedial=True, source_assignment=assignment).exists()

    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_remedial_is_idempotent(self, mock_prof, mock_agg, db, assignment, student, subpart_a, subpart_b):
        """Running grade_submission twice for the same failing student only creates one remedial."""
        from openshiksha.apps.core.models import ProblemSet, Submission
        from openshiksha.apps.core.tasks import _create_remedial_assignment, grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={
                str(subpart_a.id): 99,  # wrong
                str(subpart_b.id): 99,  # wrong
            },
        )
        grade_submission(submission.pk)

        # Call remedial creation again directly (simulates double-trigger)
        _create_remedial_assignment(submission.pk)

        remedial_count = ProblemSet.objects.filter(is_remedial=True, source_assignment=assignment).count()
        assert remedial_count == 1, "Remedial should be idempotent — only one created"
