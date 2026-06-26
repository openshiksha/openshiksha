"""
Tests for the Guided step-validator AI wrong-step explainer (GSV-3).

The load-bearing safety property: **AI never decides correctness.** The endpoint
re-runs the deterministic ``apps.core.algebra.check_step`` engine (GSV-1)
server-side and only calls the LLM when that engine has *already* ruled a step
wrong — so the tests assert the verdict for correct / wrong / unparseable lines
is the engine's, and that the AI is never invoked except on the genuine-wrong
path. Both the real (mocked-LLM) path and the deterministic fallback path are
covered, per the iron-clad bar.

Two layers:
  1. ``generate_step_hint`` — the LLM cascade + deterministic static fallback.
  2. POST /api/v1/ai/step-hint/ — wiring, auth, the deterministic verdict gate.
"""

from unittest.mock import patch

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.ai.llm_client import _stub_step_hint, generate_step_hint
from openshiksha.apps.core.models import Board, School, User, UserRole

# ─────────────────────────────────────────────────────────────
# llm_client.generate_step_hint — cascade + fallback (no DB)
# ─────────────────────────────────────────────────────────────


def _claude_text_returns(text, model="claude-sonnet-4-6"):
    return patch(
        "openshiksha.apps.ai.llm_client._call_anthropic_text",
        return_value={"text": text, "model": model, "input_tokens": 10, "output_tokens": 20},
    )


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_real_path_returns_llm_explanation():
    with _claude_text_returns("Watch the sign on the 3 — you flipped it when moving it across."):
        result = generate_step_hint("2x + 3 = 7", "2x = 10", "These equations have different solutions.")

    assert result["model"] == "claude-sonnet-4-6"
    assert "sign" in result["text"].lower()


@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_empty_llm_text_falls_back_to_stub(monkeypatch):
    # Empty/whitespace LLM output must not be shown as a real generation — it
    # falls through the cascade to the deterministic stub.
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)
    with _claude_text_returns("   "):
        result = generate_step_hint("x = 4", "x = 5", "These equations have different solutions.")

    assert result["model"] == "stub"
    assert result["text"] == _stub_step_hint()


def test_no_provider_returns_deterministic_stub(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)

    result = generate_step_hint("a + b", "a - b", "The two sides differ.")

    assert result["model"] == "stub"
    assert result["input_tokens"] == 0
    assert result["text"] == _stub_step_hint()
    assert result["text"].strip()  # never blank


def test_stub_text_is_a_generic_nudge_not_an_answer():
    text = _stub_step_hint().lower()
    # The static hint coaches a re-check; it must not assert a specific reason
    # (that's the deterministic engine's job, not this fallback's).
    assert "check" in text or "re-do" in text or "re-check" in text


# ─────────────────────────────────────────────────────────────
# POST /api/v1/ai/step-hint/ — endpoint
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def student_client(db, school):
    user = User.objects.create_user(username="s1", password="pass1234", role=UserRole.STUDENT, school=school)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


URL = "/api/v1/ai/step-hint/"


@pytest.mark.django_db
def test_requires_authentication():
    resp = APIClient().post(URL, {"previous": "x = 4", "current": "x = 5"}, format="json")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_missing_field_is_400(student_client):
    resp = student_client.post(URL, {"previous": "x = 4"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_wrong_step_real_path_returns_ai_hint(student_client):
    # 2x + 3 = 7  →  2x = 10 is a wrong move (should be 2x = 4): the deterministic
    # engine rules it wrong, and the AI explains it.
    with _claude_text_returns("You subtracted 3 from only one side — take it off the 7 too."):
        resp = student_client.post(URL, {"previous": "2x + 3 = 7", "current": "2x = 10"}, format="json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "wrong"
    assert body["ai_available"] is True
    assert body["model_used"] == "claude-sonnet-4-6"
    assert "subtracted" in body["hint"].lower()


@pytest.mark.django_db
def test_wrong_step_fallback_path_returns_static_hint(student_client, monkeypatch):
    # No LLM provider: the wrong-step verdict still stands (deterministic) and the
    # hint is the honest static fallback — graceful, not a 500, not stub-as-real.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    monkeypatch.setattr("openshiksha.apps.ai.llm_client._ollama_reachable", lambda _url: False)

    resp = student_client.post(URL, {"previous": "2x + 3 = 7", "current": "2x = 10"}, format="json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "wrong"
    assert body["ai_available"] is False
    assert body["model_used"] == "stub"
    assert body["hint"] == _stub_step_hint()


@pytest.mark.django_db
def test_correct_step_never_calls_ai(student_client):
    # 2x + 3 = 7  →  2x = 4 is a valid move: the engine says correct, and the AI
    # is never invoked (patch would raise if it were).
    with patch("openshiksha.apps.ai.views.generate_step_hint", side_effect=AssertionError("AI must not run")):
        resp = student_client.post(URL, {"previous": "2x + 3 = 7", "current": "2x = 4"}, format="json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "correct"
    assert body["hint"] is None
    assert body["model_used"] is None
    assert body["ai_available"] is False


@pytest.mark.django_db
def test_unparseable_line_never_calls_ai(student_client):
    # A malformed line is the deterministic engine's fallback (verdict, not 500);
    # there's no grounded wrong-step to explain, so AI is never invoked.
    with patch("openshiksha.apps.ai.views.generate_step_hint", side_effect=AssertionError("AI must not run")):
        resp = student_client.post(URL, {"previous": "2x + 3 = 7", "current": "2x = ="}, format="json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "unparseable"
    assert body["hint"] is None
    assert body["ai_available"] is False


@pytest.mark.django_db
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
def test_unexpected_ai_error_degrades_to_static_hint(student_client):
    # An unexpected exception inside generation must not 500 — it degrades to the
    # honest static fallback, with verdict still the deterministic "wrong".
    with patch("openshiksha.apps.ai.views.generate_step_hint", side_effect=RuntimeError("boom")):
        resp = student_client.post(URL, {"previous": "2x + 3 = 7", "current": "2x = 10"}, format="json")

    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "wrong"
    assert body["ai_available"] is False
    assert body["hint"] == _stub_step_hint()
