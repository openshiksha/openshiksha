"""
Tests for Describe-to-Build AI widget authoring (DTB-2).

Two layers:
  1. ``generate_widget_config`` — the LLM orchestration + deterministic guardrail.
     Every path (real, clamp-repaired, un-salvageable, no-provider) must return a
     **schema-valid** config; the LLM output never escapes raw.
  2. POST /api/v1/ai/widget-authoring/ — wiring, teacher-only permission, shape.
"""

from unittest.mock import patch

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.ai.llm_client import _best_guess_widget_kind, generate_widget_config
from openshiksha.apps.core.models import Board, School, User, UserRole
from openshiksha.apps.core.widgets import AI_AUTHORABLE_WIDGET_KINDS, SAFE_DEFAULT_CONFIGS, is_valid_widget_config

# ─────────────────────────────────────────────────────────────
# llm_client.generate_widget_config — guardrail (no DB)
# ─────────────────────────────────────────────────────────────


def _claude_returns(widget_kind, widget_config, variable_constraints=None):
    """Patch the shared Claude tool caller to return a fixed widget proposal."""
    data = {"widget_kind": widget_kind, "widget_config": widget_config}
    if variable_constraints is not None:
        data["variable_constraints"] = variable_constraints
    return patch(
        "openshiksha.apps.ai.llm_client._call_anthropic_tool",
        return_value={
            "data": data,
            "model": "claude-sonnet-4-6",
            "input_tokens": 10,
            "output_tokens": 20,
        },
    )


def test_best_guess_kind_is_grounded_in_the_words():
    assert _best_guess_widget_kind("shade 3/4 of a fraction bar") == "fraction-bar"
    assert _best_guess_widget_kind("plot the parabola y = x^2") == "function-plotter"
    assert _best_guess_widget_kind("a piston that does work on a gas") == "thermo-piston"
    assert _best_guess_widget_kind("mark the integer on the number line") == "number-line"
    # Nothing recognisable → safest answer-producing default.
    assert _best_guess_widget_kind("???") == "number-line"


def test_safe_defaults_are_all_schema_valid():
    """The deterministic fallbacks must themselves pass validation, for every kind."""
    for kind in AI_AUTHORABLE_WIDGET_KINDS:
        assert kind in SAFE_DEFAULT_CONFIGS
        assert is_valid_widget_config(kind, SAFE_DEFAULT_CONFIGS[kind])


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_real_path_valid_config_passes_through():
    with _claude_returns("fraction-bar", {"numerator": 3, "denominator": 4, "mode": "shaded"}):
        result = generate_widget_config("a bar showing three quarters")

    assert result["ai_available"] is True
    assert result["repaired"] is False
    assert result["model"] == "claude-sonnet-4-6"
    assert result["widget_kind"] == "fraction-bar"
    assert result["widget_config"] == {"numerator": 3, "denominator": 4, "mode": "shaded"}
    # Iron-clad: whatever comes back is schema-valid.
    assert is_valid_widget_config(result["widget_kind"], result["widget_config"])


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_real_path_out_of_bounds_config_is_clamp_repaired():
    """An out-of-bounds + unknown-key proposal is salvaged, not rejected or shown raw."""
    bad = {"denominator": 1000, "numerator": 2, "mode": "rainbow", "bogus": True}
    with _claude_returns("fraction-bar", bad):
        result = generate_widget_config("a fraction bar")

    assert result["ai_available"] is True
    assert result["repaired"] is True
    cfg = result["widget_config"]
    assert cfg["denominator"] == 40  # clamped to schema maximum
    assert cfg["numerator"] == 2  # in-bounds, preserved
    assert "bogus" not in cfg  # additionalProperties: false
    assert "mode" not in cfg  # invalid enum value dropped
    assert is_valid_widget_config(result["widget_kind"], cfg)


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_real_path_unsalvageable_output_falls_to_safe_default():
    """Wrong kind + non-dict config → deterministic default, honestly flagged."""
    with _claude_returns("not-a-real-kind", "definitely not a config"):
        result = generate_widget_config("mark a point on the number line")

    assert result["ai_available"] is False  # honest provenance — it's a default
    assert result["model"] == "stub"
    assert result["widget_kind"] == "number-line"
    assert result["widget_config"] == SAFE_DEFAULT_CONFIGS["number-line"]
    assert is_valid_widget_config(result["widget_kind"], result["widget_config"])


def test_fallback_path_no_provider_returns_safe_default(monkeypatch):
    """No key + Ollama down → deterministic safe default, never a 500 or stub-as-real."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)

    result = generate_widget_config("plot y = x squared")

    assert result["ai_available"] is False
    assert result["model"] == "stub"
    assert result["widget_kind"] == "function-plotter"
    assert is_valid_widget_config(result["widget_kind"], result["widget_config"])


# ─────────────────────────────────────────────────────────────
# DTB-5 — variable-aware generation (no DB)
# ─────────────────────────────────────────────────────────────


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_variable_aware_keeps_backed_tokens_and_returns_constraints():
    config = {"min": "{{lo}}", "max": "{{hi}}", "label": "Mark the fraction"}
    constraints = {"lo": {"min": 0, "max": 2, "integer": True}, "hi": {"min": 8, "max": 10, "integer": True}}
    with _claude_returns("number-line", config, constraints):
        result = generate_widget_config("a number line marking a random point", allow_variables=True)

    assert result["ai_available"] is True
    assert result["widget_config"] == config  # both tokens backed → preserved
    assert result["variable_constraints"]["lo"] == {"min": 0, "max": 2, "integer": True}
    assert is_valid_widget_config(result["widget_kind"], result["widget_config"])


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_variable_aware_drops_unbacked_token():
    # {{hi}} has no constraint → its field is dropped; the config stays valid.
    config = {"min": "{{lo}}", "max": "{{hi}}"}
    with _claude_returns("number-line", config, {"lo": {"min": 0, "max": 3, "integer": True}}):
        result = generate_widget_config("randomise the low end", allow_variables=True)

    assert result["widget_config"] == {"min": "{{lo}}"}
    assert set(result["variable_constraints"]) == {"lo"}
    assert result["repaired"] is True  # dropping the unbacked field is a repair
    assert is_valid_widget_config(result["widget_kind"], result["widget_config"])


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_variables_stripped_when_not_allowed():
    # Default (allow_variables=False): a stray token must never escape, and no
    # constraints come back — DTB-2/3 callers get a fully-concrete config.
    config = {"min": "{{lo}}", "max": 10}
    with _claude_returns("number-line", config, {"lo": {"min": 0, "max": 2, "integer": True}}):
        result = generate_widget_config("a plain number line")

    assert result["widget_config"] == {"max": 10}
    assert result["variable_constraints"] == {}


def test_stub_proposal_has_no_variables(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)

    result = generate_widget_config("a random fraction bar", allow_variables=True)

    assert result["ai_available"] is False  # deterministic default is never randomised
    assert result["variable_constraints"] == {}


# ─────────────────────────────────────────────────────────────
# POST /api/v1/ai/widget-authoring/ — endpoint
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def teacher_client(db, school):
    user = User.objects.create_user(username="t1", password="pass1234", role=UserRole.TEACHER, school=school)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def student_client(db, school):
    user = User.objects.create_user(username="s1", password="pass1234", role=UserRole.STUDENT, school=school)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/widget-authoring/"


@pytest.mark.django_db
def test_endpoint_success_returns_proposal(teacher_client):
    mock_result = {
        "widget_kind": "number-line",
        "widget_config": {"min": 0, "max": 1, "step": 0.25, "label": "Mark 3/4"},
        "model": "claude-sonnet-4-6",
        "ai_available": True,
        "repaired": False,
    }
    with patch("openshiksha.apps.ai.views.generate_widget_config", return_value=mock_result) as mock_gen:
        response = teacher_client.post(URL, {"description": "a number line where students mark 3/4"}, format="json")

    assert response.status_code == 200, response.data
    assert response.data["widget_kind"] == "number-line"
    assert response.data["widget_config"]["step"] == 0.25
    assert response.data["model_used"] == "claude-sonnet-4-6"
    assert response.data["ai_available"] is True
    assert response.data["repaired"] is False
    mock_gen.assert_called_once_with(
        description="a number line where students mark 3/4", kind_hint=None, allow_variables=False
    )


@pytest.mark.django_db
def test_endpoint_passes_kind_hint(teacher_client):
    mock_result = {
        "widget_kind": "fraction-bar",
        "widget_config": SAFE_DEFAULT_CONFIGS["fraction-bar"],
        "model": "stub",
        "ai_available": False,
        "repaired": False,
    }
    with patch("openshiksha.apps.ai.views.generate_widget_config", return_value=mock_result) as mock_gen:
        response = teacher_client.post(
            URL, {"description": "show a quarter", "kind_hint": "fraction-bar"}, format="json"
        )

    assert response.status_code == 200, response.data
    # Stub returned → honestly reported as not AI-generated.
    assert response.data["ai_available"] is False
    mock_gen.assert_called_once_with(description="show a quarter", kind_hint="fraction-bar", allow_variables=False)


@pytest.mark.django_db
def test_endpoint_passes_allow_variables_and_returns_constraints(teacher_client):
    mock_result = {
        "widget_kind": "number-line",
        "widget_config": {"min": "{{lo}}", "max": 10},
        "model": "claude-sonnet-4-6",
        "ai_available": True,
        "repaired": False,
        "variable_constraints": {"lo": {"min": 0, "max": 3, "integer": True}},
    }
    with patch("openshiksha.apps.ai.views.generate_widget_config", return_value=mock_result) as mock_gen:
        response = teacher_client.post(
            URL,
            {"description": "a number line marking a random point", "allow_variables": True},
            format="json",
        )

    assert response.status_code == 200, response.data
    assert response.data["variable_constraints"] == {"lo": {"min": 0, "max": 3, "integer": True}}
    mock_gen.assert_called_once_with(
        description="a number line marking a random point", kind_hint=None, allow_variables=True
    )


@pytest.mark.django_db
def test_endpoint_defaults_allow_variables_false_and_empty_constraints(teacher_client):
    mock_result = {
        "widget_kind": "number-line",
        "widget_config": {"min": 0, "max": 10, "step": 1, "label": "Mark"},
        "model": "claude-sonnet-4-6",
        "ai_available": True,
        "repaired": False,
        "variable_constraints": {},
    }
    with patch("openshiksha.apps.ai.views.generate_widget_config", return_value=mock_result) as mock_gen:
        response = teacher_client.post(URL, {"description": "a number line"}, format="json")

    assert response.status_code == 200, response.data
    assert response.data["variable_constraints"] == {}
    mock_gen.assert_called_once_with(description="a number line", kind_hint=None, allow_variables=False)


@pytest.mark.django_db
def test_endpoint_forbidden_for_students(student_client):
    response = student_client.post(URL, {"description": "a number line"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_endpoint_requires_description(teacher_client):
    response = teacher_client.post(URL, {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_endpoint_unauthenticated():
    client = APIClient()
    response = client.post(URL, {"description": "a number line"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_endpoint_llm_unexpected_error_returns_503(teacher_client):
    with patch("openshiksha.apps.ai.views.generate_widget_config", side_effect=RuntimeError("boom")):
        response = teacher_client.post(URL, {"description": "a number line"}, format="json")
    assert response.status_code == 503
