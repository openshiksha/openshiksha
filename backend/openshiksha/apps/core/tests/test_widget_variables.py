"""
Tests for the DTB-5 variable-aware authoring guardrail.

Two pure (no-DB) layers, both deterministic and LLM-free:

  1. ``apps.core.widgets.reconcile_widget_variables`` — pairs a config's
     ``{{var}}`` bindings with validated croupier constraints, dropping any token
     that has no valid backing constraint so a literal ``{{var}}`` can never reach
     the runtime.
  2. ``apps.api.croupier.substitute_typed`` — resolves a pure ``{{token}}`` leaf
     to its variable's **native typed value** (so a numeric widget field arrives
     as a number, not the string ``"3"``) and keeps mixed strings as strings.
"""

import pytest

from openshiksha.apps.api.croupier import sample_variable_values, substitute_typed
from openshiksha.apps.core.widgets import is_valid_widget_config, reconcile_widget_variables

# ─────────────────────────────────────────────────────────────
# reconcile_widget_variables — the deterministic guardrail
# ─────────────────────────────────────────────────────────────


def test_token_with_valid_constraint_is_kept_and_paired():
    config = {"min": "{{lo}}", "max": "{{hi}}", "label": "Mark the value"}
    raw = {
        "lo": {"min": 0, "max": 2, "integer": True},
        "hi": {"min": 8, "max": 10, "integer": True},
    }
    out_config, constraints = reconcile_widget_variables("number-line", config, raw)

    assert out_config == config  # both tokens backed → nothing dropped
    assert set(constraints) == {"lo", "hi"}
    assert constraints["lo"] == {"min": 0, "max": 2, "integer": True}
    # The reconciled config is still schema-valid (tokens are type-tolerant).
    assert is_valid_widget_config("number-line", out_config)


def test_token_without_constraint_is_dropped():
    # ``max`` is bound to {{hi}} but no constraint declares it → drop the field
    # (falls back to the kind default) so no literal token leaks to the runtime.
    config = {"min": "{{lo}}", "max": "{{hi}}"}
    raw = {"lo": {"min": 0, "max": 3, "integer": True}}
    out_config, constraints = reconcile_widget_variables("number-line", config, raw)

    assert out_config == {"min": "{{lo}}"}
    assert "max" not in out_config
    assert set(constraints) == {"lo"}
    assert is_valid_widget_config("number-line", out_config)


def test_unreferenced_constraints_are_dropped():
    config = {"min": "{{lo}}", "max": 10}
    raw = {
        "lo": {"min": 0, "max": 2, "integer": True},
        "unused": {"min": 1, "max": 9, "integer": True},
    }
    _out, constraints = reconcile_widget_variables("number-line", config, raw)
    assert set(constraints) == {"lo"}


@pytest.mark.parametrize(
    "bad_spec",
    [
        {"min": 5, "max": 1, "integer": True},  # min > max
        {"min": "a", "max": 9},  # non-numeric bound
        {"min": True, "max": 9},  # bool is not a numeric bound
        {"max": 9},  # missing min
        "not-a-dict",  # spec isn't even an object
    ],
)
def test_malformed_constraint_drops_its_token(bad_spec):
    config = {"min": "{{lo}}"}
    out_config, constraints = reconcile_widget_variables("number-line", config, {"lo": bad_spec})
    # Invalid constraint → token unbacked → field dropped, no dangling constraint.
    assert out_config == {}
    assert constraints == {}


def test_float_var_decimals_clamped_and_defaulted():
    raw = {
        "a": {"min": 0.0, "max": 1.0, "integer": False, "decimals": 99},
        "b": {"min": 0.0, "max": 1.0, "integer": False},  # decimals defaults to 2
    }
    config = {"min": "{{a}}", "max": "{{b}}"}
    _out, constraints = reconcile_widget_variables("number-line", config, raw)
    assert constraints["a"]["decimals"] == 6  # clamped to the cap
    assert constraints["b"]["decimals"] == 2  # default


def test_empty_constraints_strips_all_tokens():
    # The non-variable-aware path: passing {} must remove every token binding.
    config = {"min": "{{lo}}", "max": 10, "label": "Mark it"}
    out_config, constraints = reconcile_widget_variables("number-line", config, {})
    assert out_config == {"max": 10, "label": "Mark it"}
    assert constraints == {}


def test_non_dict_config_is_safe():
    assert reconcile_widget_variables("number-line", "nope", {"a": {"min": 0, "max": 1}}) == ({}, {})


def test_constraints_feed_real_per_student_randomisation():
    """The whole point: the emitted constraints actually randomise per student,
    deterministically and within the declared bounds (AI authors, croupier
    samples, grader is untouched)."""
    config = {"min": "{{lo}}", "max": "{{hi}}"}
    raw = {
        "lo": {"min": 0, "max": 2, "integer": True},
        "hi": {"min": 8, "max": 10, "integer": True},
    }
    _out, constraints = reconcile_widget_variables("number-line", config, raw)

    subpart_id = 4321
    v_alice = sample_variable_values(constraints, student_id=1, subpart_id=subpart_id)
    v_bob = sample_variable_values(constraints, student_id=2, subpart_id=subpart_id)

    # Stable per student (reproducible at grading time)…
    assert v_alice == sample_variable_values(constraints, student_id=1, subpart_id=subpart_id)
    # …within the AI-declared bounds…
    assert 0 <= v_alice["lo"] <= 2 and 8 <= v_alice["hi"] <= 10
    assert 0 <= v_bob["lo"] <= 2 and 8 <= v_bob["hi"] <= 10
    # …and at least one student differs from another across a spread of ids
    # (the randomisation is real, not a constant).
    samples = [sample_variable_values(constraints, student_id=i, subpart_id=subpart_id)["lo"] for i in range(1, 12)]
    assert len(set(samples)) > 1


# ─────────────────────────────────────────────────────────────
# croupier.substitute_typed — typed leaf resolution
# ─────────────────────────────────────────────────────────────


def test_pure_token_resolves_to_native_int():
    out = substitute_typed("{{lo}}", {"lo": 3})
    assert out == 3 and isinstance(out, int)  # NOT the string "3"


def test_pure_token_resolves_to_native_float():
    out = substitute_typed("{{s}}", {"s": 0.25})
    assert out == 0.25 and isinstance(out, float)


def test_pure_token_expression_is_typed():
    out = substitute_typed("{{a+1}}", {"a": 4})
    assert out == 5 and not isinstance(out, str)


def test_mixed_string_stays_a_string():
    assert substitute_typed("value {{a}}", {"a": 4}) == "value 4"


def test_unknown_token_left_intact():
    # No value for the var → leave the literal token rather than raise/blank.
    assert substitute_typed("{{missing}}", {}) == "{{missing}}"


def test_non_string_passes_through():
    assert substitute_typed(7, {"a": 1}) == 7
    assert substitute_typed(None, {}) is None
