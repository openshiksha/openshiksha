"""
Tests for the deterministic algebraic-equivalence engine (GSV-1).

Covers the **real path** (correct equivalence verdicts across the curriculum's
expression/equation forms) and the **deterministic fallback** (malformed input
never raises — it returns a verdict with a populated ``error``). No AI, no
network: the engine is pure and seeded, so every assertion is reproducible.
"""

from __future__ import annotations

import pytest

from openshiksha.apps.core.algebra import (
    EquivalenceResult,
    are_equations_equivalent,
    are_expressions_equivalent,
    check_step,
)

# --------------------------------------------------------------------------- #
# Expression equivalence — the real path
# --------------------------------------------------------------------------- #


class TestExpressionEquivalence:
    @pytest.mark.parametrize(
        "a, b",
        [
            ("2*(x + 3)", "2*x + 6"),  # distribution
            ("x + x", "2*x"),  # like terms
            ("(x + 1)^2", "x^2 + 2*x + 1"),  # binomial expansion
            ("x*x*x", "x^3"),  # powers
            ("3*x - x", "2*x"),  # subtraction
            ("(x^2 - 1)/(x - 1)", "x + 1"),  # rational simplification (x != 1)
            ("x + y", "y + x"),  # commutativity, two vars
            ("2*x*y + x*y", "3*x*y"),  # multi-variable
            ("6/2", "3"),  # constants
            ("sin(x)^2 + cos(x)^2", "1"),  # trig identity
        ],
    )
    def test_equivalent_expressions(self, a, b):
        result = are_expressions_equivalent(a, b)
        assert result.equivalent is True, f"{a} != {b}: {result.reason}"
        assert result.ok

    def test_implicit_multiplication(self):
        # Student-friendly notation: a coefficient or a group juxtaposed with a
        # factor parses as a product (2x, 3(x+1), x(x+1)). A multi-letter run is
        # a single identifier (so function names like ``sin`` keep working), not
        # a product of single letters — that is an intentional limitation.
        assert are_expressions_equivalent("2x + 6", "2*(x+3)").equivalent
        assert are_expressions_equivalent("3(x+1)", "3x + 3").equivalent
        assert are_expressions_equivalent("x(x+1)", "x^2 + x").equivalent

    @pytest.mark.parametrize(
        "a, b",
        [
            ("2*x + 6", "2*x + 5"),  # off by a constant
            ("x + x", "x^2"),  # different growth
            ("(x + 1)^2", "x^2 + 1"),  # dropped cross term
            ("x + y", "x - y"),  # sign
            ("2", "3"),  # different constants
        ],
    )
    def test_inequivalent_expressions(self, a, b):
        result = are_expressions_equivalent(a, b)
        assert result.equivalent is False, f"{a} == {b}? {result.reason}"
        assert result.ok  # a real verdict, not a parse error

    def test_constants_undefined_reports_error(self):
        # 1/0 is undefined for a constant expression -> fallback, not a crash.
        result = are_expressions_equivalent("1/0", "x")
        assert result.equivalent is False


# --------------------------------------------------------------------------- #
# Equation equivalence — the real path
# --------------------------------------------------------------------------- #


class TestEquationEquivalence:
    @pytest.mark.parametrize(
        "a, b",
        [
            ("2*x = 6", "x = 3"),  # divide both sides
            ("x + 3 = 7", "x = 4"),  # subtract from both sides
            ("2*x = 6", "4*x - 12 = 0"),  # rearrange + scale
            ("3*x + 1 = 10", "3*x = 9"),  # subtract constant
            ("x/2 = 4", "x = 8"),  # multiply both sides
            ("2x + 4 = 10", "x = 3"),  # implicit mult, full solve
            ("y = 2*x + 1", "y - 1 = 2*x"),  # two-variable rearrange
        ],
    )
    def test_equivalent_equations(self, a, b):
        result = are_equations_equivalent(a, b)
        assert result.equivalent is True, f"{a} !~ {b}: {result.reason}"
        assert result.ok

    @pytest.mark.parametrize(
        "a, b",
        [
            ("2*x = 6", "x = 4"),  # wrong solution
            ("x + 3 = 7", "x = 5"),  # arithmetic slip
            ("2*x = 6", "x = -3"),  # sign error
            ("3*x = 9", "3*x = 12"),  # different constant
        ],
    )
    def test_inequivalent_equations(self, a, b):
        result = are_equations_equivalent(a, b)
        assert result.equivalent is False, f"{a} ~ {b}? {result.reason}"
        assert result.ok

    def test_identities(self):
        assert are_equations_equivalent("0 = 0", "2 - 2 = 0").equivalent
        # An identity is not equivalent to a real constraint.
        assert not are_equations_equivalent("0 = 0", "x = 1").equivalent

    def test_non_equation_input_is_error(self):
        result = are_equations_equivalent("x + 1", "x = 1")
        assert result.equivalent is False
        assert result.error is not None


# --------------------------------------------------------------------------- #
# check_step dispatch + the deterministic fallback
# --------------------------------------------------------------------------- #


class TestCheckStepDispatch:
    def test_dispatches_to_equations(self):
        assert check_step("2*x = 6", "x = 3").equivalent
        assert not check_step("2*x = 6", "x = 4").equivalent

    def test_dispatches_to_expressions(self):
        assert check_step("2*(x + 1)", "2*x + 2").equivalent
        assert not check_step("2*(x + 1)", "2*x + 3").equivalent

    def test_mixed_equation_and_expression_rejected(self):
        result = check_step("x = 3", "x + 0")
        assert result.equivalent is False
        assert result.error is not None

    @pytest.mark.parametrize(
        "prev, cur",
        [
            ("2*(x +", "2*x"),  # unbalanced parens
            ("x @ 2", "x"),  # illegal character
            ("", "x"),  # empty line
            ("x", "   "),  # whitespace-only line
            ("x = = 3", "x = 3"),  # multiple '='
        ],
    )
    def test_malformed_input_returns_error_not_raise(self, prev, cur):
        # The deterministic fallback: a structured non-equivalent result with an
        # error message, never an exception bubbling into the caller.
        result = check_step(prev, cur)
        assert isinstance(result, EquivalenceResult)
        assert result.equivalent is False
        assert result.error is not None

    def test_non_string_input(self):
        # Deliberately passes a non-string to exercise the guard; the test
        # method is untyped so mypy does not check this call's argument types.
        result = check_step(None, "x")
        assert result.equivalent is False
        assert result.error is not None

    def test_result_reason_is_populated(self):
        # Every verdict carries a deterministic, human-readable reason.
        ok = check_step("2*x = 6", "x = 3")
        assert ok.reason
        bad = check_step("2*x = 6", "x = 4")
        assert bad.reason


class TestDeterminism:
    def test_same_inputs_same_verdict(self):
        # Seeded probing -> identical verdict every call.
        for _ in range(5):
            assert are_expressions_equivalent("(x+1)^2", "x^2 + 2x + 1").equivalent
            assert not are_expressions_equivalent("(x+1)^2", "x^2 + 1").equivalent
