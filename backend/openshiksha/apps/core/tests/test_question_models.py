"""
Tests for Question Bank models: QuestionTag, Question, QuestionSubpart, SubjectRoom
"""

import pytest

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    ClassRoom,
    Question,
    QuestionSubpart,
    QuestionTag,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=8)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher_user(db, school):
    return User.objects.create_user(username="teacher1", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student_user(db, school):
    return User.objects.create_user(username="student1", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def question(db, school, standard, subject, chapter):
    return Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)


class TestQuestionTag:
    def test_create_tag(self, db):
        tag = QuestionTag.objects.create(name="Quadratic Equations", tag_type="concept")
        assert tag.name == "Quadratic Equations"
        assert tag.tag_type == "concept"

    def test_tag_name_unique(self, db):
        QuestionTag.objects.create(name="Unique Tag")
        with pytest.raises(IntegrityError):
            QuestionTag.objects.create(name="Unique Tag")

    def test_default_tag_type_is_concept(self, db):
        tag = QuestionTag.objects.create(name="Some Tag")
        assert tag.tag_type == "concept"

    def test_str(self, db):
        tag = QuestionTag.objects.create(name="Hard Problem", tag_type="difficulty")
        assert "Hard Problem" in str(tag)
        assert "difficulty" in str(tag)


class TestQuestion:
    def test_create_question(self, question):
        assert question.pk is not None
        assert question.difficulty == 2
        assert question.is_active is True

    def test_default_question_type_is_mcq(self, question):
        assert question.question_type == "mcq"

    def test_difficulty_range_validation(self, db, school, standard, subject, chapter):
        q = Question(school=school, standard=standard, subject=subject, chapter=chapter, difficulty=6)
        with pytest.raises(ValidationError):
            q.full_clean()

    def test_difficulty_min_validation(self, db, school, standard, subject, chapter):
        q = Question(school=school, standard=standard, subject=subject, chapter=chapter, difficulty=0)
        with pytest.raises(ValidationError):
            q.full_clean()

    def test_question_soft_delete(self, question):
        question.is_active = False
        question.save()
        assert Question.objects.filter(pk=question.pk, is_active=False).exists()

    def test_null_school_is_shared_bank(self, db, standard, subject, chapter):
        q = Question.objects.create(school=None, standard=standard, subject=subject, chapter=chapter)
        assert q.school is None

    def test_tags_m2m(self, question, db):
        tag = QuestionTag.objects.create(name="Algebra Tag")
        question.tags.add(tag)
        assert question.tags.filter(pk=tag.pk).exists()


class TestQuestionSubpart:
    def test_create_subpart(self, question, db):
        subpart = QuestionSubpart.objects.create(
            question=question,
            index=0,
            correct_answer={"type": "mcq", "answer": 2},
        )
        assert subpart.index == 0
        assert subpart.correct_answer == {"type": "mcq", "answer": 2}

    def test_subpart_ordering(self, question, db):
        QuestionSubpart.objects.create(question=question, index=1, correct_answer={})
        QuestionSubpart.objects.create(question=question, index=0, correct_answer={})
        subparts = list(question.subparts.all())
        assert subparts[0].index == 0
        assert subparts[1].index == 1

    def test_unique_index_per_question(self, question, db):
        QuestionSubpart.objects.create(question=question, index=0, correct_answer={})
        with pytest.raises(IntegrityError):
            QuestionSubpart.objects.create(question=question, index=0, correct_answer={})

    def test_cascade_delete_with_question(self, question, db):
        QuestionSubpart.objects.create(question=question, index=0, correct_answer={})
        question_pk = question.pk
        question.delete()
        assert not QuestionSubpart.objects.filter(question_id=question_pk).exists()

    def test_solution_hint_default_empty(self, question, db):
        subpart = QuestionSubpart.objects.create(question=question, index=0, correct_answer={})
        assert subpart.solution_text == ""
        assert subpart.hint_text == ""


class TestSubjectRoom:
    def test_create_subject_room(self, db, classroom, subject, teacher_user):
        room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher_user)
        assert room.pk is not None
        assert room.is_active is True

    def test_unique_per_classroom_subject(self, db, classroom, subject, teacher_user):
        SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher_user)
        with pytest.raises(IntegrityError):
            SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher_user)

    def test_students_m2m(self, db, classroom, subject, teacher_user, student_user):
        room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher_user)
        room.students.add(student_user)
        assert room.students.filter(pk=student_user.pk).exists()

    def test_str(self, db, classroom, subject, teacher_user):
        room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher_user)
        assert subject.name in str(room)


class TestStudentSerializerSolutionGating:
    def test_solution_hidden_without_grading_flag(self, question, db):
        from openshiksha.apps.api.serializers.core import QuestionSubpartStudentSerializer

        subpart = QuestionSubpart.objects.create(
            question=question, index=0, correct_answer={}, solution_text="The steps", hint_text="A nudge"
        )
        data = QuestionSubpartStudentSerializer(subpart, context={}).data
        assert "solution_text" not in data
        assert data["hint_text"] == "A nudge"

    def test_solution_shown_when_graded(self, question, db):
        from openshiksha.apps.api.serializers.core import QuestionSubpartStudentSerializer

        subpart = QuestionSubpart.objects.create(
            question=question, index=0, correct_answer={}, solution_text="The steps"
        )
        data = QuestionSubpartStudentSerializer(subpart, context={"include_solutions": True}).data
        assert data["solution_text"] == "The steps"
