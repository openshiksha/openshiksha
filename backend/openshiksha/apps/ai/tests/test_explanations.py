"""
Tests for the Natural Language Explanations feature.

Covers:
- SubpartExplanation model creation and constraints
- llm_client stub path (no API key)
- generate_explanations_for_submission Celery task (mocked LLM)
- generate_explanation_for_subpart Celery task (mocked LLM)
- API: GET /api/v1/ai/explanations/ list + filter
- API: GET /api/v1/ai/explanations/{id}/ retrieve
- API: POST /api/v1/ai/explanations/generate/ on-demand
"""

from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────


def make_board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.get_or_create(name="CBSE")[0]


def make_school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.get_or_create(name="Test School", board=board)[0]


def make_standard(db, number=8):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.get_or_create(number=number)[0]


def make_subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.get_or_create(name="Mathematics")[0]


def make_chapter(db, subject, standard, name="Algebra"):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.get_or_create(name=name, subject=subject, standard=standard)[0]


_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


def make_classroom(db, school, standard):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


def make_subject_room(db, classroom, subject, teacher):
    from openshiksha.apps.core.models import SubjectRoom

    return SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)


def make_question(db, standard, subject, chapter):
    from openshiksha.apps.core.models import Question, QuestionType

    return Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=2,
    )


def make_subpart(db, question, index=0, question_text="What is 2 + 2?"):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(
        question=question,
        index=index,
        question_text=question_text,
        options=[
            {"key": "A", "text": "3"},
            {"key": "B", "text": "4"},
            {"key": "C", "text": "5"},
        ],
        correct_answer={"type": "mcq", "answer": "B"},
    )


def make_problem_set(db, standard, subject, chapter):
    from openshiksha.apps.core.models import ProblemSet

    return ProblemSet.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Test PS",
        number=1,
    )


def make_assignment(db, subject_room, problem_set, teacher):
    from openshiksha.apps.core.models import Assignment

    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher,
        due_at=timezone.now() + timezone.timedelta(days=7),
    )


def make_submission(db, assignment, student, answers=None):
    from openshiksha.apps.core.models import Submission

    # Leave submitted_at=None so the post_save signal does NOT trigger grade_submission.
    # Tests that need ticks create them directly via make_tick().
    return Submission.objects.create(
        assignment=assignment,
        student=student,
        answers=answers or {},
        score=0.5,
        completion=1.0,
    )


def make_tick(db, student, subpart, submission, subject_room, mark=1.0):
    from openshiksha.apps.edge.models import Tick

    return Tick.objects.create(
        student=student,
        question_subpart=subpart,
        submission=submission,
        subject_room=subject_room,
        mark=mark,
    )


@pytest.fixture
def setup(db):
    board = make_board(db)
    school = make_school(db, board)
    standard = make_standard(db)
    subject = make_subject(db)
    chapter = make_chapter(db, subject, standard)
    teacher = make_user(db, role="teacher", username="teacher_exp")
    student = make_user(db, role="student", username="student_exp", grade=8)
    classroom = make_classroom(db, school, standard)
    classroom.students.add(student)
    subject_room = make_subject_room(db, classroom, subject, teacher)
    subject_room.students.add(student)
    question = make_question(db, standard, subject, chapter)
    subpart = make_subpart(db, question)
    problem_set = make_problem_set(db, standard, subject, chapter)
    problem_set.questions.add(question)
    assignment = make_assignment(db, subject_room, problem_set, teacher)
    submission = make_submission(db, assignment, student, answers={str(subpart.id): "B"})
    tick = make_tick(db, student, subpart, submission, subject_room, mark=1.0)
    return {
        "student": student,
        "teacher": teacher,
        "subpart": subpart,
        "submission": submission,
        "tick": tick,
        "subject_room": subject_room,
    }


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_subpart_explanation_create(setup):
    from openshiksha.apps.ai.models import SubpartExplanation

    exp = SubpartExplanation.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        submission=setup["submission"],
        student_answer="B",
        is_correct=True,
        explanation_text="Great job! 2+2=4 because you are adding two groups of 2.",
        language="en",
        grade_level=8,
        model_used="stub",
        input_tokens=50,
        output_tokens=30,
    )

    assert exp.pk is not None
    assert exp.is_correct is True
    assert "2+2" in exp.explanation_text


@pytest.mark.django_db
def test_subpart_explanation_unique_together(setup):
    from django.db import IntegrityError

    from openshiksha.apps.ai.models import SubpartExplanation

    SubpartExplanation.objects.create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        submission=setup["submission"],
        student_answer="B",
        is_correct=True,
        explanation_text="First explanation.",
        language="en",
        grade_level=8,
    )
    with pytest.raises(IntegrityError):
        SubpartExplanation.objects.create(
            student=setup["student"],
            question_subpart=setup["subpart"],
            submission=setup["submission"],
            student_answer="A",
            is_correct=False,
            explanation_text="Second explanation.",
            language="en",
            grade_level=8,
        )


# ─────────────────────────────────────────────────────────────
# llm_client stub tests
# ─────────────────────────────────────────────────────────────


def test_llm_client_stub_no_providers(monkeypatch):
    """With no keys and Ollama unreachable, llm_client returns a stub explanation."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:19999")  # nothing listening

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_explanation(
            question_text="What is 2+2?",
            options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
            student_answer="B",
            correct_answer={"answer": "B"},
            is_correct=True,
            grade_level=8,
        )

    assert "text" in result
    assert result["model"] == "stub"
    assert result["input_tokens"] == 0


def test_llm_client_google_gemma_path(monkeypatch):
    """With GOOGLE_AI_API_KEY set and no Anthropic key, uses Google Gemma."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "fake-google-key")

    mock_result = {"text": "Gemma says: correct!", "model": "gemini-2.5-flash", "input_tokens": 80, "output_tokens": 20}

    with patch("openshiksha.apps.ai.llm_client._call_google_ai_studio", return_value=mock_result) as mock_google:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_explanation(
            question_text="What is 2+2?",
            options=None,
            student_answer="4",
            correct_answer={"answer": "4"},
            is_correct=True,
            grade_level=6,
        )

    mock_google.assert_called_once()
    assert result["model"] == "gemini-2.5-flash"
    assert result["text"] == "Gemma says: correct!"


def test_llm_client_ollama_path(monkeypatch):
    """With no API keys but Ollama reachable, uses Ollama."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    mock_result = {
        "text": "Ollama says: try again!",
        "model": "ollama/gemma3:4b",
        "input_tokens": 40,
        "output_tokens": 15,
    }

    with (
        patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=True),
        patch("openshiksha.apps.ai.llm_client._call_ollama", return_value=mock_result) as mock_ollama,
    ):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_explanation(
            question_text="Capital of France?",
            options=None,
            student_answer="Berlin",
            correct_answer={"answer": "Paris"},
            is_correct=False,
            grade_level=9,
        )

    mock_ollama.assert_called_once()
    assert "ollama" in result["model"]


def test_llm_client_grade_tier_primary():
    from openshiksha.apps.ai.llm_client import _grade_tier

    tier = _grade_tier(5)
    assert "primary" in tier.lower()


def test_llm_client_grade_tier_middle():
    from openshiksha.apps.ai.llm_client import _grade_tier

    tier = _grade_tier(8)
    assert "middle" in tier.lower()


def test_llm_client_grade_tier_senior():
    from openshiksha.apps.ai.llm_client import _grade_tier

    tier = _grade_tier(11)
    assert "high school" in tier.lower()


def test_build_prompt_includes_question():
    from openshiksha.apps.ai.llm_client import _build_prompt

    prompt = _build_prompt(
        question_text="What is the capital of France?",
        options=[{"key": "A", "text": "Berlin"}, {"key": "B", "text": "Paris"}],
        student_answer="B",
        correct_answer={"answer": "B"},
        is_correct=True,
        grade_level=9,
        language="en",
    )
    assert "France" in prompt
    assert "Paris" in prompt


def test_build_prompt_hindi_instruction():
    from openshiksha.apps.ai.llm_client import _build_prompt

    prompt = _build_prompt(
        question_text="2+2=?",
        options=None,
        student_answer="4",
        correct_answer={"answer": "4"},
        is_correct=True,
        grade_level=6,
        language="hi",
    )
    assert "Hindi" in prompt


# ─────────────────────────────────────────────────────────────
# Celery task tests (mocked LLM)
# ─────────────────────────────────────────────────────────────

MOCK_LLM_RESULT = {
    "text": "Good work! The answer is correct because 2+2=4.",
    "model": "claude-sonnet-4-6",
    "input_tokens": 120,
    "output_tokens": 40,
}


@pytest.mark.django_db
def test_generate_explanations_for_submission(setup):
    from openshiksha.apps.ai.models import SubpartExplanation
    from openshiksha.apps.ai.tasks import generate_explanations_for_submission

    # Patch at the source module so the local import inside the task sees the mock
    with patch("openshiksha.apps.ai.llm_client.generate_explanation", return_value=MOCK_LLM_RESULT):
        result = generate_explanations_for_submission(setup["submission"].pk)

    assert result["created"] == 1
    assert result["updated"] == 0
    assert result["skipped"] == 0

    exp = SubpartExplanation.objects.get(
        student=setup["student"],
        submission=setup["submission"],
    )
    assert exp.is_correct is True
    assert exp.explanation_text == MOCK_LLM_RESULT["text"]
    assert exp.input_tokens == 120


@pytest.mark.django_db
def test_generate_explanations_idempotent(setup):
    """Calling the task twice updates rather than duplicating."""
    from openshiksha.apps.ai.models import SubpartExplanation
    from openshiksha.apps.ai.tasks import generate_explanations_for_submission

    with patch("openshiksha.apps.ai.llm_client.generate_explanation", return_value=MOCK_LLM_RESULT):
        generate_explanations_for_submission(setup["submission"].pk)
        result = generate_explanations_for_submission(setup["submission"].pk)

    assert result["created"] == 0
    assert result["updated"] == 1
    assert SubpartExplanation.objects.filter(submission=setup["submission"]).count() == 1


@pytest.mark.django_db
def test_generate_explanations_nonexistent_submission():
    from openshiksha.apps.ai.tasks import generate_explanations_for_submission

    result = generate_explanations_for_submission(999999)
    assert result == {"created": 0, "updated": 0, "skipped": 0}


@pytest.mark.django_db
def test_generate_explanation_for_subpart_task(setup):
    from openshiksha.apps.ai.models import SubpartExplanation
    from openshiksha.apps.ai.tasks import generate_explanation_for_subpart

    with patch("openshiksha.apps.ai.llm_client.generate_explanation", return_value=MOCK_LLM_RESULT):
        result = generate_explanation_for_subpart(
            student_id=setup["student"].pk,
            subpart_id=setup["subpart"].pk,
            student_answer="B",
            is_correct=True,
            grade_level=8,
        )

    assert "explanation_id" in result
    exp = SubpartExplanation.objects.get(pk=result["explanation_id"])
    assert exp.student == setup["student"]
    assert exp.is_correct is True


@pytest.mark.django_db
def test_generate_for_subpart_regenerates_in_place_on_language_change(setup):
    """LA-4: requesting a different language replaces the stored explanation
    (update_or_create on the (student, subpart, submission) key) instead of
    duplicating it — an explanation exists in one language at a time."""
    from openshiksha.apps.ai.models import SubpartExplanation
    from openshiksha.apps.ai.tasks import generate_explanation_for_subpart

    common = {
        "student_id": setup["student"].pk,
        "subpart_id": setup["subpart"].pk,
        "student_answer": "B",
        "is_correct": True,
        "grade_level": 8,
    }
    with patch("openshiksha.apps.ai.llm_client.generate_explanation", return_value=MOCK_LLM_RESULT):
        first = generate_explanation_for_subpart(**common, language="en")
        second = generate_explanation_for_subpart(**common, language="hi")

    assert first["explanation_id"] == second["explanation_id"]
    assert SubpartExplanation.objects.filter(student=setup["student"], question_subpart=setup["subpart"]).count() == 1
    exp = SubpartExplanation.objects.get(pk=second["explanation_id"])
    assert exp.language == "hi"


@pytest.mark.django_db
def test_generate_for_subpart_same_language_is_idempotent(setup):
    from openshiksha.apps.ai.models import SubpartExplanation
    from openshiksha.apps.ai.tasks import generate_explanation_for_subpart

    common = {
        "student_id": setup["student"].pk,
        "subpart_id": setup["subpart"].pk,
        "student_answer": "B",
        "is_correct": True,
        "grade_level": 8,
    }
    with patch("openshiksha.apps.ai.llm_client.generate_explanation", return_value=MOCK_LLM_RESULT):
        first = generate_explanation_for_subpart(**common, language="hi")
        second = generate_explanation_for_subpart(**common, language="hi")

    assert first["explanation_id"] == second["explanation_id"]
    exp = SubpartExplanation.objects.get(pk=second["explanation_id"])
    assert exp.language == "hi"
    assert SubpartExplanation.objects.filter(student=setup["student"], question_subpart=setup["subpart"]).count() == 1


# ─────────────────────────────────────────────────────────────
# API tests
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


def get_tokens(api_client, user):
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"username": user.username, "password": "pass"},
        format="json",
    )
    return resp.data["access"]


@pytest.fixture
def explanation(db, setup):
    from openshiksha.apps.ai.models import SubpartExplanation

    obj, _ = SubpartExplanation.objects.update_or_create(
        student=setup["student"],
        question_subpart=setup["subpart"],
        submission=setup["submission"],
        defaults=dict(
            student_answer="B",
            is_correct=True,
            explanation_text="Correct! The answer is 4.",
            language="en",
            grade_level=8,
            model_used="stub",
        ),
    )
    return obj


@pytest.mark.django_db
def test_api_list_explanations(api_client, setup, explanation):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.get("/api/v1/ai/explanations/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["is_correct"] is True


@pytest.mark.django_db
def test_api_list_explanations_filter_by_submission(api_client, setup, explanation):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.get(f"/api/v1/ai/explanations/?submission={setup['submission'].pk}")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_list_explanations_filter_by_subpart(api_client, setup, explanation):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.get(f"/api/v1/ai/explanations/?subpart={setup['subpart'].pk}")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_teacher_cannot_list_explanations(api_client, setup, explanation):
    """Teachers cannot access student explanations via this endpoint."""
    token = get_tokens(api_client, setup["teacher"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.get("/api/v1/ai/explanations/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_retrieve_explanation(api_client, setup, explanation):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.get(f"/api/v1/ai/explanations/{explanation.pk}/")
    assert resp.status_code == 200
    assert resp.data["explanation_text"] == "Correct! The answer is 4."


@pytest.mark.django_db
def test_api_generate_explanation_on_demand(api_client, setup):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    with patch("openshiksha.apps.ai.views.generate_explanation_for_subpart") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/explanations/generate/",
            {
                "subpart_id": setup["subpart"].pk,
                "student_answer": "B",
                "is_correct": True,
                "grade_level": 8,
                "language": "en",
            },
            format="json",
        )

    assert resp.status_code == 202
    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_api_generate_explanation_invalid_subpart(api_client, setup):
    token = get_tokens(api_client, setup["student"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.post(
        "/api/v1/ai/explanations/generate/",
        {"subpart_id": 999999, "student_answer": "B", "is_correct": False},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_generate_explanation_teacher_forbidden(api_client, setup):
    token = get_tokens(api_client, setup["teacher"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.post(
        "/api/v1/ai/explanations/generate/",
        {"subpart_id": setup["subpart"].pk, "student_answer": "B", "is_correct": True},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_unauthenticated_access(api_client):
    resp = api_client.get("/api/v1/ai/explanations/")
    assert resp.status_code == 401
