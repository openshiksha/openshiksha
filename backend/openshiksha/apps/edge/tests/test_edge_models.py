"""
Tests for edge analytics models: Tick, StudentProficiency, SubjectRoomProficiency,
SubjectRoomQuestionMistake
"""

from datetime import timedelta

import pytest

from django.utils import timezone

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    QuestionSubpart,
    QuestionTag,
    School,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import StudentProficiency, SubjectRoomProficiency, SubjectRoomQuestionMistake, Tick

# ---------------------------------------------------------------------------
# Shared fixtures (mirrors convention from core tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Edge Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Science")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Motion", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="B", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_edge", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_edge", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def tag(db):
    return QuestionTag.objects.create(name="Newton Laws", tag_type="concept")


@pytest.fixture
def question(db, school, standard, subject, chapter):
    return Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type="mcq",
    )


@pytest.fixture
def subpart(db, question):
    return QuestionSubpart.objects.create(question=question, index=0, correct_answer={"answer": 2})


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Motion Test PS",
        number=1,
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
    )


@pytest.fixture
def submission(db, assignment, student):
    return Submission.objects.create(
        assignment=assignment,
        student=student,
        answers={},
    )


@pytest.fixture
def tick(db, student, subpart, submission, subject_room):
    return Tick.objects.create(
        student=student,
        question_subpart=subpart,
        submission=submission,
        subject_room=subject_room,
        mark=0.8,
    )


# ---------------------------------------------------------------------------
# Tick tests
# ---------------------------------------------------------------------------


class TestTick:
    def test_create(self, tick):
        assert tick.pk is not None
        assert tick.mark == 0.8
        assert tick.is_acknowledged is False

    def test_str(self, tick, student, subpart):
        s = str(tick)
        assert str(student) in s or student.username in s
        assert "mark=0.8" in s

    def test_acknowledge(self, tick):
        tick.acknowledge()
        tick.refresh_from_db()
        assert tick.is_acknowledged is True

    def test_cascade_delete_with_submission(self, tick, submission):
        tick_pk = tick.pk
        submission.delete()
        assert not Tick.objects.filter(pk=tick_pk).exists()

    def test_cascade_delete_with_student(self, tick, student, submission):
        # Submission.student is PROTECT (preserve academic records), so the
        # submission must be deleted before the student can be deleted.
        tick_pk = tick.pk
        submission.delete()
        student.delete()
        assert not Tick.objects.filter(pk=tick_pk).exists()


# ---------------------------------------------------------------------------
# StudentProficiency tests
# ---------------------------------------------------------------------------


class TestStudentProficiency:
    def test_create_defaults(self, db, student, tag, subject_room):
        prof = StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        assert prof.rate == 0.0
        assert prof.score == 0.0
        assert prof.tick_count == 0

    def test_unique_together(self, db, student, tag, subject_room):
        from django.db import IntegrityError

        StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        with pytest.raises(IntegrityError):
            StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)

    def test_apply_tick_updates_rate(self, db, student, tag, subject_room, tick):
        prof = StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        prof.apply_tick(tick)
        prof.refresh_from_db()
        assert prof.tick_count == 1
        assert prof.total_marks == pytest.approx(0.8)
        assert prof.rate == pytest.approx(0.8)

    def test_apply_tick_accumulates(
        self, db, student, tag, subject_room, submission, subpart, subject_room_fixture=None
    ):
        prof = StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        tick1 = Tick(
            student=student, question_subpart=subpart, submission=submission, subject_room=subject_room, mark=1.0
        )
        tick1.save()
        tick2 = Tick(
            student=student, question_subpart=subpart, submission=submission, subject_room=subject_room, mark=0.0
        )
        tick2.save()
        prof.apply_tick(tick1)
        prof.apply_tick(tick2)
        prof.refresh_from_db()
        assert prof.tick_count == 2
        assert prof.rate == pytest.approx(0.5)

    def test_recalculate_score_formula(self, db, student, tag, subject_room, tick):
        prof = StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        prof.apply_tick(tick)  # rate = 0.8
        prof.recalculate_score(0.6)  # percentile = 0.6
        prof.refresh_from_db()
        assert prof.percentile == pytest.approx(0.6)
        # score = 0.7 * 0.8 + 0.3 * 0.6 = 0.56 + 0.18 = 0.74
        assert prof.score == pytest.approx(0.74)

    def test_calculate_score_static(self):
        score = StudentProficiency.calculate_score(0.8, 0.6)
        assert score == pytest.approx(0.74)

    def test_str(self, db, student, tag, subject_room):
        prof = StudentProficiency.objects.create(student=student, question_tag=tag, subject_room=subject_room)
        assert "score=" in str(prof)


# ---------------------------------------------------------------------------
# SubjectRoomProficiency tests
# ---------------------------------------------------------------------------


class TestSubjectRoomProficiency:
    def test_create(self, db, tag, subject_room):
        room_prof = SubjectRoomProficiency.objects.create(question_tag=tag, subject_room=subject_room)
        assert room_prof.rate == 0.0
        assert room_prof.score == 0.0

    def test_unique_together(self, db, tag, subject_room):
        from django.db import IntegrityError

        SubjectRoomProficiency.objects.create(question_tag=tag, subject_room=subject_room)
        with pytest.raises(IntegrityError):
            SubjectRoomProficiency.objects.create(question_tag=tag, subject_room=subject_room)

    def test_update_method(self, db, tag, subject_room):
        room_prof = SubjectRoomProficiency.objects.create(question_tag=tag, subject_room=subject_room)
        room_prof.update(rate=0.7, percentile=0.5)
        room_prof.refresh_from_db()
        assert room_prof.rate == pytest.approx(0.7)
        assert room_prof.score == pytest.approx(0.7 * 0.7 + 0.3 * 0.5)


# ---------------------------------------------------------------------------
# SubjectRoomQuestionMistake tests
# ---------------------------------------------------------------------------


class TestSubjectRoomQuestionMistake:
    def test_create(self, db, subject_room, question):
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        assert mistake.regression == 0.0

    def test_unique_together(self, db, subject_room, question):
        from django.db import IntegrityError

        SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        with pytest.raises(IntegrityError):
            SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)

    def test_apply_tick_full_credit(self, db, subject_room, question, tick):
        """A tick with mark=1.0 should add 0 regression."""
        tick.mark = 1.0
        tick.save()
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        mistake.apply_tick(tick, num_subparts=2)
        mistake.refresh_from_db()
        assert mistake.regression == pytest.approx(0.0)

    def test_apply_tick_no_credit(self, db, subject_room, question, tick):
        """A tick with mark=0.0 and 2 subparts should add 0.5 regression."""
        tick.mark = 0.0
        tick.save()
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        mistake.apply_tick(tick, num_subparts=2)
        mistake.refresh_from_db()
        assert mistake.regression == pytest.approx(0.5)

    def test_apply_tick_partial_credit(self, db, subject_room, question, tick):
        """A tick with mark=0.8 and 1 subpart should add 0.2 regression."""
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        mistake.apply_tick(tick, num_subparts=1)
        mistake.refresh_from_db()
        assert mistake.regression == pytest.approx(0.2)

    def test_apply_tick_zero_subparts_noop(self, db, subject_room, question, tick):
        """Zero num_subparts must not mutate regression (guard against division by zero)."""
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        mistake.apply_tick(tick, num_subparts=0)
        assert mistake.regression == 0.0

    def test_str(self, db, subject_room, question):
        mistake = SubjectRoomQuestionMistake.objects.create(subject_room=subject_room, question=question)
        assert "regression=" in str(mistake)
