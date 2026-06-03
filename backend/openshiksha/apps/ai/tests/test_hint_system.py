"""
Tests for the Intelligent Hint System feature.

Covers:
- HintSequence and StudentMisconception models
- llm_client: generate_hint_sequence + diagnose_misconception (stub / cascade / parsing)
- diagnose_misconception_for_subpart Celery task (mocked LLM)
- API: GET/POST /api/v1/ai/hints/ (synchronous generate-or-fetch, caching)
- API: GET/POST /api/v1/ai/misconceptions/ (list + queue diagnose)
"""

from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"hint_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import (
        Board,
        Chapter,
        ClassRoom,
        Question,
        QuestionSubpart,
        QuestionType,
        School,
        Standard,
        Subject,
        SubjectRoom,
    )

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="Hint School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    chapter = Chapter.objects.get_or_create(name="Fractions", subject=subject, standard=standard)[0]
    teacher = make_user(db, role="teacher", username="hint_teacher")
    student = make_user(db, role="student", username="hint_student", grade=8)
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    classroom.students.add(student)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(student)

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
        hint_text="Find a common denominator first.",
    )
    return {
        "student": student,
        "teacher": teacher,
        "subpart": subpart,
        "subject_room": subject_room,
    }


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_hint_sequence_create_and_count(setup):
    from openshiksha.apps.ai.models import HintSequence

    hs = HintSequence.objects.create(
        question_subpart=setup["subpart"],
        hints=[{"level": 1, "text": "Think about denominators."}, {"level": 2, "text": "LCM of 2 and 4 is 4."}],
        grade_level=8,
        model_used="stub",
    )
    assert hs.pk is not None
    assert hs.hint_count == 2
    assert "subpart" in str(hs)


@pytest.mark.django_db
def test_hint_sequence_one_per_subpart(setup):
    from django.db import IntegrityError

    from openshiksha.apps.ai.models import HintSequence

    HintSequence.objects.create(question_subpart=setup["subpart"], hints=[], grade_level=8)
    with pytest.raises(IntegrityError):
        HintSequence.objects.create(question_subpart=setup["subpart"], hints=[], grade_level=8)


@pytest.mark.django_db
def test_misconception_create(setup):
    from openshiksha.apps.ai.models import StudentMisconception

    mc = StudentMisconception.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        submission=None,
        student_answer="A",
        misconception_label="adds numerators and denominators",
        diagnosis_text="The student added across, getting 2/6 instead of finding a common denominator.",
        remediation_tip="Practise finding the LCM of denominators.",
        grade_level=8,
    )
    assert mc.pk is not None
    assert "adds numerators" in str(mc)


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────


def test_generate_hint_sequence_stub_uses_static_hint(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_hint_sequence(
            question_text="1/2 + 1/4?",
            options=[{"key": "A", "text": "2/6"}, {"key": "B", "text": "3/4"}],
            correct_answer={"answer": "B"},
            grade_level=8,
            num_hints=3,
            static_hint="Find a common denominator first.",
        )

    assert result["model"] == "stub"
    assert len(result["hints"]) == 1
    assert result["hints"][0]["text"] == "Find a common denominator first."
    assert result["hints"][0]["level"] == 1


def test_generate_hint_sequence_stub_generic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_hint_sequence(
            question_text="1/2 + 1/4?",
            options=None,
            correct_answer={"answer": "0.75"},
            grade_level=8,
            num_hints=3,
        )

    assert result["model"] == "stub"
    assert len(result["hints"]) == 3
    assert [h["level"] for h in result["hints"]] == [1, 2, 3]


def test_generate_hint_sequence_anthropic_tool(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    mock_tool_result = {
        "data": {"hints": [{"level": 1, "text": "Nudge"}, {"level": 2, "text": "Stronger"}]},
        "model": "claude-sonnet-4-6",
        "input_tokens": 100,
        "output_tokens": 50,
    }
    with patch("openshiksha.apps.ai.llm_client._call_anthropic_tool", return_value=mock_tool_result):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_hint_sequence(
            question_text="q",
            options=None,
            correct_answer={"answer": "x"},
            grade_level=9,
            num_hints=2,
        )

    assert result["model"] == "claude-sonnet-4-6"
    assert len(result["hints"]) == 2
    assert result["hints"][1]["text"] == "Stronger"


def test_parse_hints_renumbers_and_truncates():
    from openshiksha.apps.ai.llm_client import _parse_hints

    raw = [{"level": 5, "text": "a"}, {"text": "b"}, {"text": ""}, "c"]
    parsed = _parse_hints(raw, num_hints=2)
    assert len(parsed) == 2
    assert [h["level"] for h in parsed] == [1, 2]
    assert parsed[0]["text"] == "a"


def test_parse_hints_empty_falls_back_to_stub():
    from openshiksha.apps.ai.llm_client import _parse_hints

    parsed = _parse_hints([], num_hints=3)
    assert len(parsed) == 3


def test_diagnose_misconception_stub(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.diagnose_misconception(
            question_text="1/2 + 1/4?",
            options=[{"key": "A", "text": "2/6"}, {"key": "B", "text": "3/4"}],
            student_answer="A",
            correct_answer={"answer": "B"},
            grade_level=8,
        )

    assert result["model"] == "stub"
    assert result["misconception_label"]
    assert result["diagnosis"]


def test_diagnose_misconception_anthropic_tool(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    mock_tool_result = {
        "data": {
            "misconception_label": "adds numerators and denominators",
            "diagnosis": "Added across.",
            "remediation": "Find LCM.",
        },
        "model": "claude-sonnet-4-6",
        "input_tokens": 90,
        "output_tokens": 30,
    }
    with patch("openshiksha.apps.ai.llm_client._call_anthropic_tool", return_value=mock_tool_result):
        from openshiksha.apps.ai import llm_client

        result = llm_client.diagnose_misconception(
            question_text="q",
            options=None,
            student_answer="A",
            correct_answer={"answer": "B"},
            grade_level=8,
        )

    assert result["model"] == "claude-sonnet-4-6"
    assert result["misconception_label"] == "adds numerators and denominators"
    assert result["remediation"] == "Find LCM."


def test_build_hints_prompt_does_not_leak_answer():
    from openshiksha.apps.ai.llm_client import _build_hints_prompt

    prompt = _build_hints_prompt(
        question_text="What is 1/2 + 1/4?",
        options=[{"key": "A", "text": "2/6"}, {"key": "B", "text": "3/4"}],
        correct_answer={"answer": "B"},
        grade_level=8,
        num_hints=3,
    )
    assert "MUST NOT" in prompt
    assert "Never reveal the answer" in prompt


# ─────────────────────────────────────────────────────────────
# Celery task tests (mocked LLM)
# ─────────────────────────────────────────────────────────────

MOCK_DIAGNOSIS = {
    "misconception_label": "adds numerators and denominators",
    "diagnosis": "The student added across.",
    "remediation": "Practise common denominators.",
    "model": "claude-sonnet-4-6",
    "input_tokens": 80,
    "output_tokens": 25,
}


@pytest.mark.django_db
def test_diagnose_task_creates_misconception(setup):
    from openshiksha.apps.ai.models import StudentMisconception
    from openshiksha.apps.ai.tasks import diagnose_misconception_for_subpart

    with patch("openshiksha.apps.ai.llm_client.diagnose_misconception", return_value=MOCK_DIAGNOSIS):
        result = diagnose_misconception_for_subpart(
            student_id=setup["student"].pk,
            subpart_id=setup["subpart"].pk,
            student_answer="A",
            grade_level=8,
        )

    assert "misconception_id" in result
    mc = StudentMisconception.objects.get(pk=result["misconception_id"])
    assert mc.misconception_label == "adds numerators and denominators"
    assert mc.input_tokens == 80


@pytest.mark.django_db
def test_diagnose_task_idempotent(setup):
    from openshiksha.apps.ai.models import StudentMisconception
    from openshiksha.apps.ai.tasks import diagnose_misconception_for_subpart

    with patch("openshiksha.apps.ai.llm_client.diagnose_misconception", return_value=MOCK_DIAGNOSIS):
        diagnose_misconception_for_subpart(
            student_id=setup["student"].pk, subpart_id=setup["subpart"].pk, student_answer="A", grade_level=8
        )
        diagnose_misconception_for_subpart(
            student_id=setup["student"].pk, subpart_id=setup["subpart"].pk, student_answer="C", grade_level=8
        )

    assert StudentMisconception.objects.filter(student=setup["student"]).count() == 1


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


MOCK_HINTS = {
    "hints": [{"level": 1, "text": "Nudge"}, {"level": 2, "text": "Stronger"}],
    "model": "claude-sonnet-4-6",
    "input_tokens": 100,
    "output_tokens": 40,
}


@pytest.mark.django_db
def test_api_generate_hints_creates_and_caches(api_client, setup):
    from openshiksha.apps.ai.models import HintSequence

    auth(api_client, setup["student"])

    with patch("openshiksha.apps.ai.views.generate_hint_sequence", return_value=MOCK_HINTS) as mock_gen:
        resp1 = api_client.post(
            "/api/v1/ai/hints/generate/", {"subpart_id": setup["subpart"].pk, "num_hints": 2}, format="json"
        )
        # Second call should hit cache, not regenerate
        resp2 = api_client.post(
            "/api/v1/ai/hints/generate/", {"subpart_id": setup["subpart"].pk, "num_hints": 2}, format="json"
        )

    assert resp1.status_code == 201
    assert len(resp1.data["hints"]) == 2
    assert resp2.status_code == 200
    mock_gen.assert_called_once()  # cached on second request
    assert HintSequence.objects.filter(question_subpart=setup["subpart"]).count() == 1


@pytest.mark.django_db
def test_api_generate_hints_response_has_no_answer(api_client, setup):
    auth(api_client, setup["student"])

    with patch("openshiksha.apps.ai.views.generate_hint_sequence", return_value=MOCK_HINTS):
        resp = api_client.post("/api/v1/ai/hints/generate/", {"subpart_id": setup["subpart"].pk}, format="json")
    assert resp.status_code == 201
    assert "correct_answer" not in resp.data


@pytest.mark.django_db
def test_api_generate_hints_invalid_subpart(api_client, setup):
    auth(api_client, setup["student"])
    resp = api_client.post("/api/v1/ai/hints/generate/", {"subpart_id": 999999}, format="json")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_generate_hints_teacher_forbidden(api_client, setup):
    auth(api_client, setup["teacher"])
    resp = api_client.post("/api/v1/ai/hints/generate/", {"subpart_id": setup["subpart"].pk}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_list_hints_by_subpart(api_client, setup):
    from openshiksha.apps.ai.models import HintSequence

    HintSequence.objects.create(question_subpart=setup["subpart"], hints=[{"level": 1, "text": "x"}], grade_level=8)
    auth(api_client, setup["student"])
    resp = api_client.get(f"/api/v1/ai/hints/?subpart={setup['subpart'].pk}")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_hints_unauthenticated(api_client):
    resp = api_client.get("/api/v1/ai/hints/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_api_diagnose_queues_task(api_client, setup):
    auth(api_client, setup["student"])

    with patch("openshiksha.apps.ai.views.diagnose_misconception_for_subpart") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/misconceptions/diagnose/",
            {"subpart_id": setup["subpart"].pk, "student_answer": "A"},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_api_diagnose_invalid_subpart(api_client, setup):
    auth(api_client, setup["student"])
    resp = api_client.post(
        "/api/v1/ai/misconceptions/diagnose/",
        {"subpart_id": 999999, "student_answer": "A"},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_list_misconceptions_student_sees_own(api_client, setup):
    from openshiksha.apps.ai.models import StudentMisconception

    StudentMisconception.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        student_answer="A",
        misconception_label="adds across",
        diagnosis_text="x",
        grade_level=8,
    )
    auth(api_client, setup["student"])
    resp = api_client.get("/api/v1/ai/misconceptions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["misconception_label"] == "adds across"


@pytest.mark.django_db
def test_api_list_misconceptions_teacher_sees_class(api_client, setup):
    from openshiksha.apps.ai.models import StudentMisconception

    StudentMisconception.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        student_answer="A",
        misconception_label="adds across",
        diagnosis_text="x",
        grade_level=8,
    )
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/misconceptions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_misconception_other_student_isolated(api_client, setup):
    from openshiksha.apps.ai.models import StudentMisconception

    other = make_user(True, role="student", username="other_student")
    StudentMisconception.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        student_answer="A",
        misconception_label="adds across",
        diagnosis_text="x",
        grade_level=8,
    )
    auth(api_client, other)
    resp = api_client.get("/api/v1/ai/misconceptions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0
