"""
Tests for Croupier Phase 2: Variable substitution and safe expression evaluation.

All tests are pure unit tests — no DB access required.
"""

import pytest

from openshiksha.apps.api.croupier import safe_eval_expr, sample_variable_values, substitute_variables_for_student
from openshiksha.apps.core.tasks import _grade_subpart

CONSTRAINTS = {
    "a": {"min": 2, "max": 9, "integer": True},
    "b": {"min": 1, "max": 20, "integer": True},
    "c": {"min": 10, "max": 50, "integer": True},
}


class TestSampleVariableValues:
    def test_variable_substitution_is_deterministic(self):
        """Same student_id + subpart_id always produces the same values."""
        v1 = sample_variable_values(CONSTRAINTS, student_id=42, subpart_id=7)
        v2 = sample_variable_values(CONSTRAINTS, student_id=42, subpart_id=7)
        assert v1 == v2

    def test_variable_substitution_differs_by_student(self):
        """Two different student IDs produce different variable values."""
        v1 = sample_variable_values(CONSTRAINTS, student_id=1, subpart_id=7)
        v2 = sample_variable_values(CONSTRAINTS, student_id=2, subpart_id=7)
        # With a 2^32 seed space and 3 variables with distinct ranges, collision
        # probability is negligible; this will always pass in practice.
        assert v1 != v2

    def test_sampled_values_within_declared_bounds(self):
        """All sampled values satisfy min <= val <= max."""
        for student_id in range(1, 20):
            vals = sample_variable_values(CONSTRAINTS, student_id=student_id, subpart_id=99)
            assert CONSTRAINTS["a"]["min"] <= vals["a"] <= CONSTRAINTS["a"]["max"]
            assert CONSTRAINTS["b"]["min"] <= vals["b"] <= CONSTRAINTS["b"]["max"]
            assert CONSTRAINTS["c"]["min"] <= vals["c"] <= CONSTRAINTS["c"]["max"]

    def test_integer_constraint_produces_integer(self):
        """integer: true -> sampled value is a Python int."""
        vals = sample_variable_values(CONSTRAINTS, student_id=5, subpart_id=3)
        assert isinstance(vals["a"], int)
        assert isinstance(vals["b"], int)
        assert isinstance(vals["c"], int)

    def test_float_constraint_produces_float(self):
        """integer: false -> sampled value is a float rounded to decimals."""
        float_constraints = {
            "x": {"min": 1.0, "max": 5.0, "integer": False, "decimals": 2},
        }
        vals = sample_variable_values(float_constraints, student_id=1, subpart_id=1)
        assert isinstance(vals["x"], float)
        assert 1.0 <= vals["x"] <= 5.0


class TestSafeEvalExpr:
    def test_safe_eval_arithmetic(self):
        """safe_eval_expr evaluates ({{c}} - {{b}}) / {{a}} correctly."""
        result = safe_eval_expr("({{c}} - {{b}}) / {{a}}", {"a": 3, "b": 5, "c": 20})
        assert result == pytest.approx(5.0)

    def test_safe_eval_rejects_function_calls(self):
        """safe_eval_expr raises ValueError for function calls (no eval() risk)."""
        with pytest.raises(ValueError):
            safe_eval_expr("__import__('os')", {})

    def test_safe_eval_rejects_name_nodes(self):
        """safe_eval_expr raises ValueError for bare name references."""
        with pytest.raises(ValueError):
            safe_eval_expr("os.system('ls')", {})

    def test_safe_eval_power(self):
        assert safe_eval_expr("{{a}} ** 2", {"a": 4}) == pytest.approx(16.0)

    def test_safe_eval_unary_neg(self):
        assert safe_eval_expr("-{{a}}", {"a": 5}) == pytest.approx(-5.0)

    def test_safe_eval_constant(self):
        """A plain number string evaluates correctly (no variable tokens)."""
        assert safe_eval_expr("3.5", {}) == pytest.approx(3.5)


class TestSubstituteVariablesForStudent:
    def test_substitutes_question_text(self):
        text, _, vals = substitute_variables_for_student(
            "Solve {{a}}x + {{b}} = {{c}}",
            None,
            CONSTRAINTS,
            student_id=1,
            subpart_id=1,
        )
        assert "{{a}}" not in text
        assert "{{b}}" not in text
        assert "{{c}}" not in text
        assert str(vals["a"]) in text

    def test_substitutes_options(self):
        options = [
            {"key": "A", "text": "x = {{a}}"},
            {"key": "B", "text": "x = {{b}}"},
        ]
        _, subst_options, vals = substitute_variables_for_student(
            "Question",
            options,
            CONSTRAINTS,
            student_id=3,
            subpart_id=5,
        )
        assert subst_options is not None
        assert "{{a}}" not in subst_options[0]["text"]
        assert str(vals["a"]) in subst_options[0]["text"]

    def test_no_constraints_returns_unchanged(self):
        text, options, vals = substitute_variables_for_student(
            "Plain question",
            [{"key": "A", "text": "opt"}],
            None,
            student_id=1,
            subpart_id=1,
        )
        assert text == "Plain question"
        assert vals == {}


class TestGradingNumericVariableQuestion:
    def test_grading_numeric_variable_question(self):
        """
        End-to-end: grade a submission where correct_answer is an expression.
        Student derives x = (c - b) / a and submits the correct value.
        """
        constraints = {
            "a": {"min": 3, "max": 3, "integer": True},  # fixed: a=3
            "b": {"min": 5, "max": 5, "integer": True},  # fixed: b=5
            "c": {"min": 20, "max": 20, "integer": True},  # fixed: c=20
        }
        # (20 - 5) / 3 = 5.0
        student_id = 42
        subpart_id = 99
        correct_answer = {"type": "numeric", "answer": "({{c}} - {{b}}) / {{a}}"}

        result = _grade_subpart(
            "numeric",
            5.0,  # correct derived answer
            correct_answer,
            student_id=student_id,
            subpart_id=subpart_id,
            variable_constraints=constraints,
        )
        assert result == 1.0

    def test_grading_numeric_variable_question_wrong_answer(self):
        """Submitting the wrong numeric value for a variable question is incorrect."""
        constraints = {
            "a": {"min": 3, "max": 3, "integer": True},
            "b": {"min": 5, "max": 5, "integer": True},
            "c": {"min": 20, "max": 20, "integer": True},
        }
        correct_answer = {"type": "numeric", "answer": "({{c}} - {{b}}) / {{a}}"}

        result = _grade_subpart(
            "numeric",
            999.0,  # wrong answer
            correct_answer,
            student_id=42,
            subpart_id=99,
            variable_constraints=constraints,
        )
        assert result == 0.0

    def test_grading_numeric_constant_answer_unaffected(self):
        """Non-variable numeric questions still grade with direct comparison."""
        result = _grade_subpart(
            "numeric",
            3.5,
            {"type": "numeric", "answer": 3.5},
            student_id=42,
            subpart_id=1,
            variable_constraints=None,
        )
        assert result == 1.0

    def test_variable_seed_distinct_from_phase1(self):
        """Phase 2 seed namespace differs from Phase 1 to prevent interference."""
        from openshiksha.apps.api.croupier import _make_seed, _make_var_seed

        seed_phase1 = _make_seed(42, 7)
        seed_phase2 = _make_var_seed(42, 7)
        assert seed_phase1 != seed_phase2
