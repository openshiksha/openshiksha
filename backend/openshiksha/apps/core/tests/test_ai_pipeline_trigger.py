"""
Tests verifying that grade_submission triggers the AI analytics pipeline.

With CELERY_TASK_ALWAYS_EAGER=True (set in test settings), all tasks run
synchronously in-process, so we can assert on DB side-effects after calling
grade_submission(submission_id).
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures (minimal setup for one graded submission)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE-AI")


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="AI Test School", board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.create(name="Maths-AI")


@pytest.fixture
def chapter(db, subject, standard):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.create(name="Algebra-AI", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(school=school, standard=standard, division="AI", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="teacher_ai", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="student_ai", password="pass", role=UserRole.STUDENT, school=school)


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
def subpart(db, question):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(
        question=question,
        index=0,
        correct_answer={"answer": 1},
    )


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    from openshiksha.apps.core.models import ProblemSet

    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="AI Test PS",
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


@pytest.fixture
def submission(db, assignment, student, subpart):
    from openshiksha.apps.core.models import Submission

    return Submission.objects.create(
        assignment=assignment,
        student=student,
        answers={str(subpart.id): 1},  # correct answer
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestAIPipelineTrigger:
    """Verify grade_submission triggers AI pipeline tasks."""

    @patch("openshiksha.apps.ai.tasks.analyze_student_subject_room")
    @patch("openshiksha.apps.ai.tasks.generate_class_insights_for_subject_room")
    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_grade_submission_triggers_ai_tasks(
        self,
        mock_proficiency,
        mock_aggregates,
        mock_class_insights,
        mock_analyze,
        submission,
        student,
        subject_room,
    ):
        """After grading, analyze_student_subject_room and generate_class_insights should be called."""
        from openshiksha.apps.core.tasks import grade_submission

        mock_proficiency.delay = MagicMock()
        mock_aggregates.delay = MagicMock()
        mock_analyze.delay = MagicMock()
        mock_class_insights.delay = MagicMock()

        grade_submission(submission.pk)

        mock_analyze.delay.assert_called_once_with(student.pk, subject_room.pk)
        mock_class_insights.delay.assert_called_once_with(subject_room.pk)

    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_grade_submission_ai_tasks_called_with_correct_ids(
        self,
        mock_proficiency,
        mock_aggregates,
        submission,
        student,
        subject_room,
    ):
        """Verify the student_id and subject_room_id passed to AI tasks are correct."""
        from openshiksha.apps.core.tasks import grade_submission

        mock_proficiency.delay = MagicMock()
        mock_aggregates.delay = MagicMock()

        with (
            patch("openshiksha.apps.ai.tasks.analyze_student_subject_room") as mock_analyze,
            patch("openshiksha.apps.ai.tasks.generate_class_insights_for_subject_room") as mock_insights,
        ):
            mock_analyze.delay = MagicMock()
            mock_insights.delay = MagicMock()

            grade_submission(submission.pk)

            # Both tasks receive the correct IDs
            mock_analyze.delay.assert_called_once_with(student.pk, subject_room.pk)
            mock_insights.delay.assert_called_once_with(subject_room.pk)

    def test_analyze_student_subject_room_dispatches_all_subtasks(self, db):
        """analyze_student_subject_room should dispatch all six sub-tasks."""
        from openshiksha.apps.ai.tasks import (
            detect_learning_gaps_for_student,
            generate_daily_practice_plan,
            rebuild_learning_path,
            refresh_recommendations_for_student,
            update_performance_prediction_for_student,
            update_student_mastery,
        )

        with (
            patch.object(detect_learning_gaps_for_student, "delay") as m1,
            patch.object(update_performance_prediction_for_student, "delay") as m2,
            patch.object(refresh_recommendations_for_student, "delay") as m3,
            patch.object(update_student_mastery, "delay") as m4,
            patch.object(rebuild_learning_path, "delay") as m5,
            patch.object(generate_daily_practice_plan, "delay") as m6,
        ):
            from openshiksha.apps.ai.tasks import analyze_student_subject_room

            analyze_student_subject_room(student_id=1, subject_room_id=2)

            m1.assert_called_once_with(1, 2)
            m2.assert_called_once_with(1, 2)
            m3.assert_called_once_with(1, 2)
            m4.assert_called_once_with(1, 2)
            m5.assert_called_once_with(1, 2)
            m6.assert_called_once_with(1, 2)
