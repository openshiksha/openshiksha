"""
Tests for the propose-and-verify AI practice-problem proposer (PV-2).

Two layers:
  1. ``generate_practice_problem`` — the LLM orchestration + the PV-1 guardrail.
     Every path (real, snap-repaired, un-verifiable, no-provider) must return a
     problem PV-1's ``verify_widget_problem`` passes; the LLM proposal never
     escapes un-verified. The engine — not the LLM — decides reachability.
  2. POST /api/v1/ai/practice-problem/ — wiring, teacher-only permission, shape.
"""

from unittest.mock import patch

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.ai.llm_client import generate_practice_problem
from openshiksha.apps.core.models import Board, School, User, UserRole
from openshiksha.apps.core.problem_verifier import SAFE_DEFAULT_PROBLEM, verify_widget_problem

# ─────────────────────────────────────────────────────────────
# llm_client.generate_practice_problem — guardrail (no DB)
# ─────────────────────────────────────────────────────────────


def _claude_returns(widget_config, correct_answer):
    """Patch the shared Claude tool caller to return a fixed problem proposal."""
    return patch(
        "openshiksha.apps.ai.llm_client._call_anthropic_tool",
        return_value={
            "data": {"widget_config": widget_config, "correct_answer": correct_answer},
            "model": "claude-sonnet-4-6",
            "input_tokens": 10,
            "output_tokens": 20,
        },
    )


def _assert_verified(result):
    """Every returned problem must be one PV-1 actually passes."""
    v = verify_widget_problem(result["widget_kind"], result["widget_config"], result["correct_answer"])
    assert v.ok is True, f"returned problem failed PV-1: {v.code} {v.reason}"


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_real_path_reachable_problem_passes_through():
    with _claude_returns({"min": 0, "max": 1, "step": 0.25, "label": "Mark 3/4"}, 0.5):
        result = generate_practice_problem("mark a half on a number line")

    assert result["ai_available"] is True
    assert result["repaired"] is False
    assert result["model"] == "claude-sonnet-4-6"
    assert result["widget_kind"] == "number-line"
    assert result["correct_answer"] == {"answer": 0.5}
    assert result["verdict_code"] == "ok"
    _assert_verified(result)


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_off_grid_answer_is_snap_repaired_not_rejected():
    """The DTB-4 bug class: ¾ on a step-0.25 grid → snapped to 0.8, still shipped."""
    with _claude_returns({"min": 0, "max": 1, "step": 0.25}, 0.75):
        result = generate_practice_problem("mark three quarters")

    assert result["ai_available"] is True
    assert result["repaired"] is True  # the answer was snapped onto the grid
    assert result["correct_answer"] == {"answer": 0.8}
    _assert_verified(result)  # the shipped answer is genuinely reachable


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_out_of_bounds_config_is_clamp_repaired():
    """An unknown key + out-of-range field is salvaged; the answer stays reachable."""
    bad_config = {"min": 0, "max": 10, "step": 1, "bogus": True}
    with _claude_returns(bad_config, 4):
        result = generate_practice_problem("mark a number")

    assert result["ai_available"] is True
    assert result["repaired"] is True  # bogus key dropped
    assert "bogus" not in result["widget_config"]
    assert result["correct_answer"] == {"answer": 4}
    _assert_verified(result)


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_non_numeric_answer_falls_to_safe_default():
    """An answer the engine can never verify → the deterministic safe problem."""
    with _claude_returns({"min": 0, "max": 10, "step": 1}, "not a number"):
        result = generate_practice_problem("mark something")

    assert result["ai_available"] is False  # honest provenance — it's a default
    assert result["model"] == "stub"
    assert result["verdict_code"] == "safe_default"
    assert result["widget_config"] == SAFE_DEFAULT_PROBLEM["widget_config"]
    _assert_verified(result)


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_unsalvageable_config_falls_to_safe_default():
    with _claude_returns("definitely not a config", 3):
        result = generate_practice_problem("mark a number")

    assert result["ai_available"] is False
    assert result["model"] == "stub"
    _assert_verified(result)


def test_fallback_path_no_provider_returns_safe_default(monkeypatch):
    """No key + Ollama down → deterministic safe problem, never a 500 or stub-as-real."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)

    result = generate_practice_problem("mark 5 on a number line")

    assert result["ai_available"] is False
    assert result["model"] == "stub"
    assert result["verdict_code"] == "safe_default"
    _assert_verified(result)


# ─────────────────────────────────────────────────────────────
# POST /api/v1/ai/practice-problem/ — endpoint
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


URL = "/api/v1/ai/practice-problem/"


@pytest.mark.django_db
def test_endpoint_success_returns_problem(teacher_client):
    mock_result = {
        "widget_kind": "number-line",
        "widget_config": {"min": 0, "max": 1, "step": 0.25, "label": "Mark 3/4"},
        "correct_answer": {"answer": 0.75},
        "model": "claude-sonnet-4-6",
        "ai_available": True,
        "repaired": False,
        "verdict_code": "ok",
    }
    with patch("openshiksha.apps.ai.views.generate_practice_problem", return_value=mock_result) as mock_gen:
        response = teacher_client.post(URL, {"topic": "mark 3/4 on a number line"}, format="json")

    assert response.status_code == 200, response.data
    assert response.data["widget_kind"] == "number-line"
    assert response.data["correct_answer"] == {"answer": 0.75}
    assert response.data["model_used"] == "claude-sonnet-4-6"
    assert response.data["ai_available"] is True
    assert response.data["verdict_code"] == "ok"
    mock_gen.assert_called_once_with(topic="mark 3/4 on a number line")


@pytest.mark.django_db
def test_endpoint_reports_safe_default_honestly(teacher_client):
    mock_result = {
        "widget_kind": SAFE_DEFAULT_PROBLEM["widget_kind"],
        "widget_config": dict(SAFE_DEFAULT_PROBLEM["widget_config"]),
        "correct_answer": dict(SAFE_DEFAULT_PROBLEM["correct_answer"]),
        "model": "stub",
        "ai_available": False,
        "repaired": False,
        "verdict_code": "safe_default",
    }
    with patch("openshiksha.apps.ai.views.generate_practice_problem", return_value=mock_result):
        response = teacher_client.post(URL, {"topic": "anything"}, format="json")

    assert response.status_code == 200, response.data
    assert response.data["ai_available"] is False  # not shown as a real generation
    assert response.data["verdict_code"] == "safe_default"


@pytest.mark.django_db
def test_endpoint_forbidden_for_students(student_client):
    response = student_client.post(URL, {"topic": "mark a number"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_endpoint_requires_topic(teacher_client):
    response = teacher_client.post(URL, {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_endpoint_unauthenticated():
    client = APIClient()
    response = client.post(URL, {"topic": "mark a number"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_endpoint_llm_unexpected_error_returns_503(teacher_client):
    with patch("openshiksha.apps.ai.views.generate_practice_problem", side_effect=RuntimeError("boom")):
        response = teacher_client.post(URL, {"topic": "mark a number"}, format="json")
    assert response.status_code == 503
