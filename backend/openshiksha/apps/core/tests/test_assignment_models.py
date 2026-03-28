"""
Tests for Assignment Pipeline models: ProblemSet, Assignment, Submission
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from openshiksha.apps.core.models import (
    ProblemSet, Assignment, Submission,
    Question, SubjectRoom,
    User, UserRole, School, Board, Standard, Subject, Chapter, ClassRoom,
)


@pytest.fixture
def board(db):
    return Board.objects.create(name='CBSE')


@pytest.fixture
def school(db, board):
    return School.objects.create(name='Test School', board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name='Science')


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name='Motion', subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(
        school=school, standard=standard, division='B', academic_year='2025-26'
    )


@pytest.fixture
def teacher_user(db, school):
    return User.objects.create_user(
        username='teacher2', password='pass', role=UserRole.TEACHER, school=school
    )


@pytest.fixture
def student_user(db, school):
    return User.objects.create_user(
        username='student2', password='pass', role=UserRole.STUDENT, school=school
    )


@pytest.fixture
def subject_room(db, classroom, subject, teacher_user, student_user):
    room = SubjectRoom.objects.create(
        classroom=classroom, subject=subject, teacher=teacher_user
    )
    room.students.add(student_user)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter):
    return Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    ps = ProblemSet.objects.create(
        school=school, standard=standard, subject=subject, chapter=chapter,
        title='Motion Basics #1', number=1,
    )
    ps.questions.add(question)
    return ps


@pytest.fixture
def assignment(db, subject_room, problem_set, teacher_user):
    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher_user,
        due_at=timezone.now() + timedelta(days=7),
    )


class TestProblemSet:
    def test_create_problem_set(self, problem_set):
        assert problem_set.pk is not None
        assert problem_set.number == 1
        assert problem_set.is_active is True

    def test_unique_number_per_chapter(self, db, school, standard, subject, chapter, question):
        ProblemSet.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter,
            title='Set 1', number=1,
        )
        with pytest.raises(IntegrityError):
            ProblemSet.objects.create(
                school=school, standard=standard, subject=subject, chapter=chapter,
                title='Another Set 1', number=1,
            )

    def test_null_school_is_shared(self, db, standard, subject, chapter):
        ps = ProblemSet.objects.create(
            school=None, standard=standard, subject=subject, chapter=chapter,
            title='Shared Set', number=1,
        )
        assert ps.school is None

    def test_questions_m2m(self, problem_set, question):
        assert problem_set.questions.filter(pk=question.pk).exists()

    def test_str(self, problem_set):
        assert 'Motion Basics' in str(problem_set)


class TestAssignment:
    def test_create_assignment(self, assignment):
        assert assignment.pk is not None
        assert assignment.assigned_at is not None
        assert assignment.average_score is None  # Not yet graded
        assert assignment.completion_rate is None

    def test_score_cache_fraction_validation(self, assignment):
        assignment.average_score = 1.5
        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_completion_rate_fraction_validation(self, assignment):
        assignment.completion_rate = -0.1
        with pytest.raises(ValidationError):
            assignment.full_clean()

    def test_str(self, assignment):
        assert 'Motion Basics' in str(assignment)


class TestSubmission:
    def test_create_submission(self, db, assignment, student_user):
        sub = Submission.objects.create(
            assignment=assignment,
            student=student_user,
            answers={'1': 2, '2': 'velocity'},
        )
        assert sub.pk is not None
        assert sub.score is None  # Not graded yet
        assert sub.completion == 0.0
        assert sub.submitted_at is None  # In progress

    def test_unique_per_student_assignment(self, db, assignment, student_user):
        Submission.objects.create(assignment=assignment, student=student_user)
        with pytest.raises(IntegrityError):
            Submission.objects.create(assignment=assignment, student=student_user)

    def test_submission_score_fraction_validation(self, db, assignment, student_user):
        sub = Submission(
            assignment=assignment, student=student_user, score=1.5
        )
        with pytest.raises(ValidationError):
            sub.full_clean()

    def test_completion_fraction_validation(self, db, assignment, student_user):
        sub = Submission(
            assignment=assignment, student=student_user, completion=2.0
        )
        with pytest.raises(ValidationError):
            sub.full_clean()

    def test_submit_sets_submitted_at(self, db, assignment, student_user):
        sub = Submission.objects.create(
            assignment=assignment,
            student=student_user,
            answers={'1': 3},
            completion=1.0,
        )
        assert sub.submitted_at is None
        sub.submitted_at = timezone.now()
        sub.save()
        sub.refresh_from_db()
        assert sub.submitted_at is not None

    def test_answers_json_storage(self, db, assignment, student_user):
        answers = {'42': 3, '43': 'photosynthesis', '44': [1, 3]}
        sub = Submission.objects.create(
            assignment=assignment,
            student=student_user,
            answers=answers,
        )
        sub.refresh_from_db()
        assert sub.answers == answers

    def test_str(self, db, assignment, student_user):
        sub = Submission.objects.create(assignment=assignment, student=student_user)
        assert 'student2' in str(sub)
