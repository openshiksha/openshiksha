"""
Tests for the deterministic propose-and-verify problem verifier (PV-1).

Covers the **real path** (a well-posed problem passes; an ill-posed one — an
answer the widget can never emit — is rejected with a structured reason) and the
**deterministic fallback** (every malformed input degrades to an ``ok=False``
verdict, never an exception). No AI, no network: the verifier is pure and the
variable sampling is seeded, so every assertion is reproducible.

The keystone case is the DTB-4 bug class: on a ``number-line`` with ``step 0.25``
the value ``0.75`` (¾) snaps to ``0.8`` and is therefore **unreachable** — the
verifier must catch that the student could never mark the "correct" answer.
"""

from __future__ import annotations

import pytest

from openshiksha.apps.core.problem_verifier import (
    ANSWER_PRODUCING_WIDGET_KINDS,
    SAFE_DEFAULT_PROBLEM,
    ProblemVerdict,
    snap_literal_answer,
    verify_widget_problem,
)

# --------------------------------------------------------------------------- #
# Reachable (well-posed) literal answers — the real path
# --------------------------------------------------------------------------- #


def test_integer_grid_answer_is_reachable():
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": 7})
    assert v.ok is True
    assert v.code == "ok"
    assert v.details["nearest_reachable"] == 7


def test_half_step_answer_is_reachable():
    # step 0.5 → decimals 1 → 0.5 snaps to itself (the demo's honest case).
    v = verify_widget_problem("number-line", {"min": 0, "max": 5, "step": 0.5}, {"answer": 0.5})
    assert v.ok is True
    assert v.code == "ok"


def test_numeric_string_answer_is_reachable():
    # The grader compares via float(...), so a stringy answer is fine.
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 2}, {"answer": "4"})
    assert v.ok is True
    assert v.details["answer"] == 4.0


def test_endpoint_answer_is_reachable():
    v = verify_widget_problem("number-line", {"min": -5, "max": 5, "step": 1}, {"answer": -5})
    assert v.ok is True


def test_defaults_apply_when_config_omits_fields():
    # No min/max/step → widget defaults (0, 10, 1); 3 is on that grid.
    v = verify_widget_problem("number-line", {}, {"answer": 3})
    assert v.ok is True


# --------------------------------------------------------------------------- #
# Unreachable (ill-posed) literal answers — the keystone rejections
# --------------------------------------------------------------------------- #


def test_three_quarters_with_quarter_step_is_unreachable():
    # The DTB-4 bug: step 0.25 → decimals 1 → 0.75 snaps to 0.8.
    v = verify_widget_problem("number-line", {"min": 0, "max": 1, "step": 0.25}, {"answer": 0.75})
    assert v.ok is False
    assert v.code == "unreachable"
    assert v.details["nearest_reachable"] == 0.8


def test_off_grid_answer_is_unreachable():
    # step 2 grid is 0,2,4,…; 3 is between grid points.
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 2}, {"answer": 3})
    assert v.ok is False
    assert v.code == "unreachable"
    assert v.details["nearest_reachable"] in (2, 4)


def test_out_of_range_answer_is_unreachable():
    # 50 is above max → clamps to 10, so it can never be marked.
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": 50})
    assert v.ok is False
    assert v.code == "unreachable"
    assert v.details["nearest_reachable"] == 10


def test_non_numeric_answer_on_answer_producing_kind_is_rejected():
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": "photosynthesis"})
    assert v.ok is False
    assert v.code == "answer_not_numeric"


def test_bool_answer_is_not_numeric():
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": True})
    assert v.ok is False
    assert v.code == "answer_not_numeric"


# --------------------------------------------------------------------------- #
# Structural / malformed input — deterministic fallback, never raises
# --------------------------------------------------------------------------- #


def test_invalid_config_is_rejected():
    # step must be > 0 (schema exclusiveMinimum) → invalid config.
    v = verify_widget_problem("number-line", {"step": -1}, {"answer": 0})
    assert v.ok is False
    assert v.code == "invalid_config"


def test_unknown_kind_is_rejected():
    v = verify_widget_problem("not-a-widget", {}, {"answer": 1})
    assert v.ok is False
    assert v.code == "invalid_config"


def test_missing_answer_is_rejected():
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, {})
    assert v.ok is False
    assert v.code == "no_answer"


def test_correct_answer_not_a_dict_is_rejected():
    v = verify_widget_problem("number-line", {"min": 0, "max": 10, "step": 1}, "0.5")
    assert v.ok is False
    assert v.code == "no_answer"


@pytest.mark.parametrize("bad_config", [None, "x", 5, []])
def test_non_dict_config_never_raises(bad_config):
    v = verify_widget_problem("number-line", bad_config, {"answer": 1})
    assert isinstance(v, ProblemVerdict)
    assert v.ok is False


# --------------------------------------------------------------------------- #
# Explanatory kinds — the widget doesn't constrain the answer field
# --------------------------------------------------------------------------- #


def test_explanatory_kind_passes_with_any_well_formed_answer():
    # fraction-bar is explanatory; the student answers in the free field, so the
    # widget bounds nothing on a grid — we verify only well-formedness.
    v = verify_widget_problem("fraction-bar", {"numerator": 1, "denominator": 4}, {"answer": "1/4"})
    assert v.ok is True
    assert v.code == "ok_explanatory"
    assert "fraction-bar" not in ANSWER_PRODUCING_WIDGET_KINDS


def test_explanatory_kind_still_validates_config():
    # denominator 0 violates exclusiveMinimum → invalid even for explanatory.
    v = verify_widget_problem("fraction-bar", {"denominator": 0}, {"answer": "x"})
    assert v.ok is False
    assert v.code == "invalid_config"


def test_explanatory_kind_still_requires_an_answer():
    v = verify_widget_problem("fraction-bar", {"numerator": 1, "denominator": 4}, {})
    assert v.ok is False
    assert v.code == "no_answer"


# --------------------------------------------------------------------------- #
# Variable-aware problems — well-posed for *every* sampled student
# --------------------------------------------------------------------------- #


def test_variable_answer_reachable_for_all_students():
    # answer == {{a}} on an integer 1..9 grid of step 1: always on the grid.
    v = verify_widget_problem(
        "number-line",
        {"min": 0, "max": 10, "step": 1, "initial": "{{a}}"},
        {"answer": "{{a}}"},
        variable_constraints={"a": {"min": 1, "max": 9, "integer": True}},
    )
    assert v.ok is True
    assert v.code == "ok_variable"
    assert v.details["sample_size"] == 8


def test_variable_answer_unreachable_for_some_students():
    # {{a}}/4 over a=1..9 produces 0.25, 0.5, … ; step 1 grid → most are off-grid.
    v = verify_widget_problem(
        "number-line",
        {"min": 0, "max": 10, "step": 1},
        {"answer": "{{a}} / 4"},
        variable_constraints={"a": {"min": 1, "max": 9, "integer": True}},
    )
    assert v.ok is False
    assert v.code == "unreachable_for_some"
    assert "variable_values" in v.details


def test_variable_path_is_deterministic():
    args = (
        "number-line",
        {"min": 0, "max": 10, "step": 1},
        {"answer": "{{a}} / 4"},
    )
    kw = {"variable_constraints": {"a": {"min": 1, "max": 9, "integer": True}}}
    first = verify_widget_problem(*args, **kw)
    second = verify_widget_problem(*args, **kw)
    assert (first.ok, first.code, first.details) == (second.ok, second.code, second.details)


def test_unparseable_variable_expression_is_graceful():
    v = verify_widget_problem(
        "number-line",
        {"min": 0, "max": 10, "step": 1},
        {"answer": "{{a}} +"},  # malformed expression
        variable_constraints={"a": {"min": 1, "max": 9, "integer": True}},
    )
    assert v.ok is False
    assert v.code == "answer_not_numeric"


def test_variable_token_without_constraints_falls_back_to_literal_path():
    # No constraints → not the variable path; the literal "{{a}}" isn't numeric.
    v = verify_widget_problem(
        "number-line",
        {"min": 0, "max": 10, "step": 1},
        {"answer": "{{a}}"},
    )
    assert v.ok is False
    assert v.code == "answer_not_numeric"


# --------------------------------------------------------------------------- #
# PV-2 guardrail helpers — snap-repair + the safe-default problem
# --------------------------------------------------------------------------- #


def test_safe_default_problem_is_verified_reachable():
    """The deterministic fallback must itself pass PV-1 — never ship an unverified default."""
    v = verify_widget_problem(
        SAFE_DEFAULT_PROBLEM["widget_kind"],
        SAFE_DEFAULT_PROBLEM["widget_config"],
        SAFE_DEFAULT_PROBLEM["correct_answer"],
    )
    assert v.ok is True


def test_snap_repairs_the_dtb4_off_grid_answer():
    # ¾ on a step-0.25 axis snaps to 0.8 — snapping makes the answer reachable.
    config = {"min": 0, "max": 1, "step": 0.25}
    repaired = snap_literal_answer("number-line", config, {"answer": 0.75})
    assert repaired == {"answer": 0.8}
    # And the repaired answer now verifies (snap is idempotent → reachable).
    assert verify_widget_problem("number-line", config, repaired).ok is True


def test_snap_repairs_an_out_of_range_answer():
    config = {"min": 0, "max": 10, "step": 1}
    repaired = snap_literal_answer("number-line", config, {"answer": 42})
    assert repaired == {"answer": 10}  # clamped into range, on the grid
    assert verify_widget_problem("number-line", config, repaired).ok is True


def test_snap_preserves_an_already_reachable_answer():
    config = {"min": 0, "max": 10, "step": 1}
    repaired = snap_literal_answer("number-line", config, {"answer": 7})
    assert repaired == {"answer": 7}


def test_snap_preserves_extra_answer_keys():
    config = {"min": 0, "max": 10, "step": 1}
    repaired = snap_literal_answer("number-line", config, {"answer": 6.4, "tolerance": 0.1})
    assert repaired == {"answer": 6, "tolerance": 0.1}


def test_snap_returns_none_for_non_numeric_answer():
    assert snap_literal_answer("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": "abc"}) is None


def test_snap_returns_none_for_variable_expression():
    # A {{var}} answer can't be fixed by snapping a single value.
    assert snap_literal_answer("number-line", {"min": 0, "max": 10, "step": 1}, {"answer": "{{a}}+1"}) is None


def test_snap_returns_none_for_missing_answer():
    assert snap_literal_answer("number-line", {"min": 0, "max": 10, "step": 1}, {}) is None
    assert snap_literal_answer("number-line", {"min": 0, "max": 10, "step": 1}, "not-a-dict") is None


def test_snap_returns_none_for_non_answer_producing_kind():
    # Explanatory kinds don't bound the answer — nothing on a grid to snap.
    assert snap_literal_answer("fraction-bar", {"numerator": 1, "denominator": 2}, {"answer": 3}) is None
