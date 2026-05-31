"""
Tests for per-student variable substitution in solution_text and hint_text on
QuestionSubpartStudentSerializer (added 2026-05-30).

The substitution must use the SAME seeded values as the question body, so a
student's worked solution references the numbers they actually saw in the
question — not a fresh sample, not the unsubstituted ``{{var}}`` token.
"""

import pytest

from rest_framework.test import APIRequestFactory

from openshiksha.apps.api.croupier import sample_variable_values
from openshiksha.apps.api.serializers.core import QuestionSubpartStudentSerializer
from openshiksha.apps.core.models import (
    Board,
    Chapter,
    Question,
    QuestionSubpart,
    QuestionType,
    School,
    Standard,
    Subject,
    User,
    UserRole,
)


@pytest.fixture
def numeric_subpart(db):
    board = Board.objects.create(name="Test Board")
    school = School.objects.create(name="Test School", board=board)
    standard = Standard.objects.create(number=8)
    subject = Subject.objects.create(name="Math")
    chapter = Chapter.objects.create(name="Geometry", subject=subject, standard=standard)
    question = Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.NUMERIC,
    )
    return QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text="Diameter is {{2*k}}cm and total height is {{j+k+k}}cm. Find r.",
        correct_answer={"type": "numeric", "answer": "{{k}}"},
        variable_constraints={
            "j": {"min": 3, "max": 3, "integer": True},
            "k": {"min": 4, "max": 4, "integer": True},
        },
        solution_text="r = {{k}}, so 2r = {{2*k}}",
        hint_text="Recall: r = diameter / 2 = {{k}}",
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(
        username="sub_test_student",
        email="sub@test.example",
        password="x",
        role=UserRole.STUDENT,
    )


def _serialize(subpart, student, include_solutions: bool):
    request = APIRequestFactory().get("/")
    request.user = student
    serializer = QuestionSubpartStudentSerializer(
        subpart,
        context={"request": request, "include_solutions": include_solutions},
    )
    return serializer.data


class TestSolutionAndHintSubstitution:
    def test_question_text_substitutes_expression_tokens(self, numeric_subpart, student):
        data = _serialize(numeric_subpart, student, include_solutions=True)
        # k=4, so 2*k=8 and j+k+k=3+4+4=11
        assert "{{2*k}}" not in data["question_text"]
        assert "{{j+k+k}}" not in data["question_text"]
        assert "8cm" in data["question_text"]
        assert "11cm" in data["question_text"]

    def test_solution_substitutes_bare_var(self, numeric_subpart, student):
        data = _serialize(numeric_subpart, student, include_solutions=True)
        assert "{{k}}" not in data["solution_text"]
        # k=4, 2*k=8 — both in solution text
        assert "r = 4" in data["solution_text"]
        assert "2r = 8" in data["solution_text"]

    def test_hint_substitutes_with_same_values(self, numeric_subpart, student):
        data = _serialize(numeric_subpart, student, include_solutions=False)
        # solution must be hidden when not graded
        assert "solution_text" not in data
        # hint always passes through and must have the same seeded values
        assert "{{k}}" not in data["hint_text"]
        assert "= 4" in data["hint_text"]

    def test_no_constraints_solution_passes_through_unchanged(self, db, student):
        Board.objects.create(name="B")
        standard = Standard.objects.create(number=9)
        subject = Subject.objects.create(name="S")
        chapter = Chapter.objects.create(name="C", subject=subject, standard=standard)
        question = Question.objects.create(
            standard=standard, subject=subject, chapter=chapter, question_type=QuestionType.FILL_BLANK
        )
        sp = QuestionSubpart.objects.create(
            question=question,
            index=0,
            question_text="Plain question.",
            solution_text="Plain solution.",
            hint_text="Plain hint.",
            variable_constraints=None,
            correct_answer={"type": "fill_blank", "answer": "x"},
        )
        data = _serialize(sp, student, include_solutions=True)
        assert data["solution_text"] == "Plain solution."
        assert data["hint_text"] == "Plain hint."

    def test_deterministic_across_requests_for_same_student(self, numeric_subpart, student):
        """Same student should always see the same substituted solution (seed = student_id, subpart_id)."""
        a = _serialize(numeric_subpart, student, include_solutions=True)
        b = _serialize(numeric_subpart, student, include_solutions=True)
        assert a["solution_text"] == b["solution_text"]
        assert a["hint_text"] == b["hint_text"]

    def test_sampled_values_match_independent_sampler(self, numeric_subpart, student):
        """The serializer's sampled values must match what sample_variable_values returns for the same seed."""
        values = sample_variable_values(numeric_subpart.variable_constraints, student.id, numeric_subpart.id)
        data = _serialize(numeric_subpart, student, include_solutions=True)
        assert str(values["k"]) in data["solution_text"]
