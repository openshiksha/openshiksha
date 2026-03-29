"""
Tests for grading task helpers and the grade_submission Celery task.

grade_submission is integration-tested against a real DB (uses pytest-django).
_grade_subpart is unit-tested without DB.
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone

from openshiksha.apps.core.tasks import _grade_subpart


# ---------------------------------------------------------------------------
# _grade_subpart — pure unit tests (no DB)
# ---------------------------------------------------------------------------

class TestGradeSubpart:
    """Tests for the subpart grading function."""

    def test_mcq_correct(self):
        assert _grade_subpart('mcq', 2, {'answer': 2}) == 1.0

    def test_mcq_wrong(self):
        assert _grade_subpart('mcq', 3, {'answer': 2}) == 0.0

    def test_mcq_string_comparison(self):
        # Answers may come in as strings from JSON
        assert _grade_subpart('mcq', '2', {'answer': 2}) == 1.0

    def test_fill_blank_correct(self):
        assert _grade_subpart('fill_blank', 'photosynthesis', {'answer': 'photosynthesis'}) == 1.0

    def test_fill_blank_wrong(self):
        assert _grade_subpart('fill_blank', 'respiration', {'answer': 'photosynthesis'}) == 0.0

    def test_numeric_exact(self):
        assert _grade_subpart('numeric', 9.8, {'answer': 9.8}) == 1.0

    def test_numeric_within_tolerance(self):
        assert _grade_subpart('numeric', 9.800001, {'answer': 9.8}) == 1.0

    def test_numeric_outside_tolerance(self):
        assert _grade_subpart('numeric', 9.9, {'answer': 9.8}) == 0.0

    def test_numeric_non_numeric_answer(self):
        assert _grade_subpart('numeric', 'not a number', {'answer': 9.8}) == 0.0

    def test_matching_full_credit(self):
        assert _grade_subpart('matching', {'a': '1', 'b': '2'}, {'answer': {'a': '1', 'b': '2'}}) == 1.0

    def test_matching_partial_credit(self):
        # 1 of 2 pairs correct → 0.5
        result = _grade_subpart('matching', {'a': '1', 'b': 'X'}, {'answer': {'a': '1', 'b': '2'}})
        assert result == pytest.approx(0.5)

    def test_matching_no_credit(self):
        assert _grade_subpart('matching', {'a': 'X', 'b': 'X'}, {'answer': {'a': '1', 'b': '2'}}) == 0.0

    def test_matching_empty_expected(self):
        assert _grade_subpart('matching', {}, {'answer': {}}) == 0.0

    def test_matching_wrong_types(self):
        assert _grade_subpart('matching', 'not a dict', {'answer': {'a': '1'}}) == 0.0

    def test_missing_answer_key(self):
        assert _grade_subpart('mcq', 2, {}) == 0.0

    def test_empty_correct_answer(self):
        assert _grade_subpart('mcq', 2, None) == 0.0

    def test_multi_select_correct(self):
        assert _grade_subpart('multi_select', '[1,2]', {'answer': '[1,2]'}) == 1.0

    def test_unknown_question_type(self):
        # Unknown types should return 0.0 gracefully
        assert _grade_subpart('essay', 'some text', {'answer': 'some text'}) == 0.0


# ---------------------------------------------------------------------------
# grade_submission — integration tests with real DB
# ---------------------------------------------------------------------------

@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board
    return Board.objects.create(name='CBSE')


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School
    return School.objects.create(name='Grading Test School', board=board)


@pytest.fixture
def standard(db):
    from openshiksha.apps.core.models import Standard
    return Standard.objects.create(number=10)


@pytest.fixture
def subject(db):
    from openshiksha.apps.core.models import Subject
    return Subject.objects.create(name='Physics')


@pytest.fixture
def chapter(db, subject, standard):
    from openshiksha.apps.core.models import Chapter
    return Chapter.objects.create(name='Forces', subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    from openshiksha.apps.core.models import ClassRoom
    return ClassRoom.objects.create(
        school=school, standard=standard, division='C', academic_year='2025-26'
    )


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole
    return User.objects.create_user(
        username='teacher_grading', password='pass', role=UserRole.TEACHER, school=school
    )


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole
    return User.objects.create_user(
        username='student_grading', password='pass', role=UserRole.STUDENT, school=school
    )


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    from openshiksha.apps.core.models import SubjectRoom
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question_mcq(db, school, standard, subject, chapter):
    from openshiksha.apps.core.models import Question
    return Question.objects.create(
        school=school, standard=standard, subject=subject, chapter=chapter,
        question_type='mcq',
    )


@pytest.fixture
def subpart_a(db, question_mcq):
    from openshiksha.apps.core.models import QuestionSubpart
    return QuestionSubpart.objects.create(
        question=question_mcq, index=0, correct_answer={'answer': 2}
    )


@pytest.fixture
def subpart_b(db, question_mcq):
    from openshiksha.apps.core.models import QuestionSubpart
    return QuestionSubpart.objects.create(
        question=question_mcq, index=1, correct_answer={'answer': 4}
    )


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question_mcq):
    from openshiksha.apps.core.models import ProblemSet
    ps = ProblemSet.objects.create(
        school=school, standard=standard, subject=subject, chapter=chapter,
        title='Forces PS', number=1,
    )
    ps.questions.add(question_mcq)
    return ps


@pytest.fixture
def assignment(db, problem_set, subject_room, teacher):
    from openshiksha.apps.core.models import Assignment
    return Assignment.objects.create(
        problem_set=problem_set, subject_room=subject_room, assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def submission_with_answers(db, assignment, student, subpart_a, subpart_b):
    from openshiksha.apps.core.models import Submission
    return Submission.objects.create(
        assignment=assignment,
        student=student,
        answers={
            str(subpart_a.id): 2,    # correct
            str(subpart_b.id): 3,    # wrong
        },
    )


class TestGradeSubmissionTask:
    @patch('openshiksha.apps.core.tasks._update_assignment_aggregates')
    @patch('openshiksha.apps.core.tasks.update_proficiency')
    def test_grade_submission_creates_ticks(
        self, mock_prof, mock_agg, submission_with_answers, subpart_a, subpart_b
    ):
        """grade_submission should create one Tick per answered subpart."""
        from openshiksha.apps.core.tasks import grade_submission
        from openshiksha.apps.edge.models import Tick

        # Call task synchronously (no Celery broker needed)
        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        result = grade_submission(submission_with_answers.pk)

        assert result['ticks_created'] == 2
        assert Tick.objects.filter(submission=submission_with_answers).count() == 2

    @patch('openshiksha.apps.core.tasks._update_assignment_aggregates')
    @patch('openshiksha.apps.core.tasks.update_proficiency')
    def test_grade_submission_score(
        self, mock_prof, mock_agg, submission_with_answers
    ):
        """score should be 0.5 (1 correct out of 2 subparts)."""
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        result = grade_submission(submission_with_answers.pk)

        assert result['score'] == pytest.approx(0.5)
        assert result['completion'] == pytest.approx(1.0)
        assert result['total_subparts'] == 2
        assert result['attempted'] == 2

    @patch('openshiksha.apps.core.tasks._update_assignment_aggregates')
    @patch('openshiksha.apps.core.tasks.update_proficiency')
    def test_grade_submission_saves_score_to_db(
        self, mock_prof, mock_agg, submission_with_answers
    ):
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        grade_submission(submission_with_answers.pk)
        submission_with_answers.refresh_from_db()
        assert submission_with_answers.score == pytest.approx(0.5)

    def test_grade_submission_missing_submission(self, db):
        from openshiksha.apps.core.tasks import grade_submission

        result = grade_submission(99999)
        assert 'error' in result

    @patch('openshiksha.apps.core.tasks._update_assignment_aggregates')
    @patch('openshiksha.apps.core.tasks.update_proficiency')
    def test_grade_submission_partial_answers(
        self, mock_prof, mock_agg, assignment, student, subpart_a, subpart_b
    ):
        """If student only answered one subpart, completion should be 0.5."""
        from openshiksha.apps.core.models import Submission
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={str(subpart_a.id): 2},  # only one answer
        )
        result = grade_submission(submission.pk)
        assert result['attempted'] == 1
        assert result['total_subparts'] == 2
        assert result['completion'] == pytest.approx(0.5)
