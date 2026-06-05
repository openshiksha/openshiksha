"""
Tests for the AI Tutor (student-facing Socratic chat) feature.

Covers:
- TutorConversation / TutorMessage models
- llm_client.generate_tutor_reply (stub / cascade / answer guard-rail)
- API: POST /api/v1/ai/tutor/ (start, with and without first message)
- API: POST /api/v1/ai/tutor/{id}/message/ (follow-up turn)
- API: GET list + retrieve, ownership scoping, student-only permission
"""

from unittest.mock import patch

import pytest

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"tutor_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Chapter, Question, QuestionSubpart, QuestionType, Standard, Subject

    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    chapter = Chapter.objects.get_or_create(name="Fractions", subject=subject, standard=standard)[0]
    student = make_user(db, role="student", username="tutor_student", grade=8)
    other_student = make_user(db, role="student", username="tutor_other", grade=8)
    teacher = make_user(db, role="teacher", username="tutor_teacher")

    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=2,
    )
    subpart = QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text="What is 1/2 + 1/4?",
        options=[
            {"key": "A", "text": "2/6"},
            {"key": "B", "text": "3/4"},
            {"key": "C", "text": "1/6"},
        ],
        correct_answer={"type": "mcq", "answer": "B"},
    )
    return {
        "student": student,
        "other_student": other_student,
        "teacher": teacher,
        "subpart": subpart,
    }


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_conversation_and_messages(setup):
    from openshiksha.apps.ai.models import TutorConversation, TutorMessage, TutorMessageRole

    convo = TutorConversation.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        title="help with fractions",
        grade_level=8,
    )
    TutorMessage.objects.create(conversation=convo, role=TutorMessageRole.STUDENT, content="I'm stuck")
    TutorMessage.objects.create(
        conversation=convo, role=TutorMessageRole.TUTOR, content="What have you tried?", model_used="stub"
    )

    assert convo.message_count == 2
    # Ordered oldest-first
    roles = list(convo.messages.values_list("role", flat=True))
    assert roles == ["student", "tutor"]
    assert "help with fractions" in str(convo)


@pytest.mark.django_db
def test_subpart_set_null_on_delete(setup):
    """Deleting the anchored subpart keeps the conversation (SET_NULL)."""
    from openshiksha.apps.ai.models import TutorConversation

    convo = TutorConversation.objects.create(student=setup["student"], question_subpart=setup["subpart"])
    setup["subpart"].delete()
    convo.refresh_from_db()
    assert convo.question_subpart_id is None


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────


def _no_providers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")


def test_generate_tutor_reply_stub(monkeypatch):
    _no_providers(monkeypatch)
    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_tutor_reply(
            student_message="How do I add 1/2 and 1/4?",
            history=[],
            question_text="What is 1/2 + 1/4?",
            options=[{"key": "B", "text": "3/4"}],
            correct_answer={"answer": "B"},
            grade_level=8,
        )

    assert result["model"] == "stub"
    assert result["text"]  # never empty
    assert result["input_tokens"] == 0


def test_stub_reply_differs_first_vs_followup():
    from openshiksha.apps.ai.llm_client import _stub_tutor_reply

    first = _stub_tutor_reply(history=[], student_message="hi")
    follow = _stub_tutor_reply(
        history=[{"role": "tutor", "content": "What have you tried?"}],
        student_message="I added the tops",
    )
    assert first != follow


def test_system_prompt_hides_answer_but_passes_guardrail():
    from openshiksha.apps.ai.llm_client import _build_tutor_system_prompt

    prompt = _build_tutor_system_prompt(
        question_text="What is 1/2 + 1/4?",
        options=[{"key": "B", "text": "3/4"}],
        correct_answer={"answer": "B"},
        grade_level=8,
        language="en",
    )
    # The correct answer text is present as a guard-rail, with a no-reveal rule.
    assert "3/4" in prompt
    assert "NEVER" in prompt


def test_generate_tutor_reply_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    mock_result = {
        "text": "What do the denominators need to be the same first?",
        "model": "claude-sonnet-4-6",
        "input_tokens": 120,
        "output_tokens": 30,
    }
    with patch("openshiksha.apps.ai.llm_client._call_anthropic_chat", return_value=mock_result) as m:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_tutor_reply(
            student_message="I'm stuck",
            history=[{"role": "tutor", "content": "What have you tried?"}],
            grade_level=8,
        )

    assert result["model"] == "claude-sonnet-4-6"
    # System + mapped messages were passed; history role mapped tutor->assistant.
    messages = m.call_args[0][1]
    assert messages[0]["role"] == "assistant"
    assert messages[-1] == {"role": "user", "content": "I'm stuck"}


def test_anthropic_chat_messages_mapping():
    from openshiksha.apps.ai.llm_client import _anthropic_chat_messages

    history = [
        {"role": "student", "content": "Q1"},
        {"role": "tutor", "content": "A1"},
        {"role": "student", "content": ""},  # skipped (empty)
    ]
    msgs = _anthropic_chat_messages(history, "Q2")
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]
    assert msgs[-1]["content"] == "Q2"


# ─────────────────────────────────────────────────────────────
# API tests
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


def auth(api_client, user):
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"username": user.username, "password": "pass"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


MOCK_REPLY = {
    "text": "Good start! What do the two fractions need before you can add them?",
    "model": "claude-sonnet-4-6",
    "input_tokens": 100,
    "output_tokens": 20,
}


@pytest.mark.django_db
def test_api_start_conversation_with_message(api_client, setup):
    from openshiksha.apps.ai.models import TutorConversation

    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", return_value=MOCK_REPLY):
        resp = api_client.post(
            "/api/v1/ai/tutor/",
            {"subpart_id": setup["subpart"].pk, "message": "How do I add these?"},
            format="json",
        )

    assert resp.status_code == 201
    assert resp.data["question_subpart"] == setup["subpart"].pk
    assert resp.data["title"] == "How do I add these?"
    roles = [m["role"] for m in resp.data["messages"]]
    assert roles == ["student", "tutor"]
    assert resp.data["messages"][1]["content"] == MOCK_REPLY["text"]
    # Reply never leaks the correct answer field.
    assert "correct_answer" not in resp.data
    convo = TutorConversation.objects.get(pk=resp.data["id"])
    assert convo.student == setup["student"]


@pytest.mark.django_db
def test_api_start_conversation_without_message(api_client, setup):
    auth(api_client, setup["student"])
    resp = api_client.post("/api/v1/ai/tutor/", {"subpart_id": setup["subpart"].pk}, format="json")
    assert resp.status_code == 201
    assert resp.data["messages"] == []


@pytest.mark.django_db
def test_api_follow_up_message(api_client, setup):
    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", return_value=MOCK_REPLY):
        start = api_client.post("/api/v1/ai/tutor/", {"message": "Help"}, format="json")
        convo_id = start.data["id"]
        resp = api_client.post(
            f"/api/v1/ai/tutor/{convo_id}/message/",
            {"message": "I think I add the tops and bottoms"},
            format="json",
        )

    assert resp.status_code == 200
    assert len(resp.data["messages"]) == 4  # 2 student + 2 tutor


@pytest.mark.django_db
def test_api_empty_followup_rejected(api_client, setup):
    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", return_value=MOCK_REPLY):
        start = api_client.post("/api/v1/ai/tutor/", {"message": "Help"}, format="json")
    resp = api_client.post(f"/api/v1/ai/tutor/{start.data['id']}/message/", {"message": "   "}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_invalid_subpart(api_client, setup):
    auth(api_client, setup["student"])
    resp = api_client.post("/api/v1/ai/tutor/", {"subpart_id": 999999, "message": "hi"}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_list_scoped_to_owner(api_client, setup):
    # student creates a conversation
    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", return_value=MOCK_REPLY):
        api_client.post("/api/v1/ai/tutor/", {"message": "mine"}, format="json")

    # other student sees none of it
    auth(api_client, setup["other_student"])
    resp = api_client.get("/api/v1/ai/tutor/")
    assert resp.status_code == 200
    results = resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data
    assert results == []


@pytest.mark.django_db
def test_api_teacher_forbidden(api_client, setup):
    auth(api_client, setup["teacher"])
    resp = api_client.post("/api/v1/ai/tutor/", {"message": "hi"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_other_student_cannot_retrieve(api_client, setup):
    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", return_value=MOCK_REPLY):
        start = api_client.post("/api/v1/ai/tutor/", {"message": "secret"}, format="json")
    convo_id = start.data["id"]

    auth(api_client, setup["other_student"])
    resp = api_client.get(f"/api/v1/ai/tutor/{convo_id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_service_unavailable_on_llm_failure(api_client, setup):
    auth(api_client, setup["student"])
    with patch("openshiksha.apps.ai.views.generate_tutor_reply", side_effect=RuntimeError("boom")):
        resp = api_client.post("/api/v1/ai/tutor/", {"message": "hi"}, format="json")
    assert resp.status_code == 503
    # Conversation + student message are preserved.
    assert "conversation" in resp.data
