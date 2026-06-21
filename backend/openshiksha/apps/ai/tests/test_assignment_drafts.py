"""
Tests for the Teacher AI Assistant — Auto-Drafted Assignments feature.

Covers:
- AssignmentDraft model: creation, properties (question_count / is_actionable), __str__
- analytics.rank_weak_chapters_for_room + build_assignment_draft: weak-chapter ranking,
  question selection, recency exclusion, allocation, empty/no-question fallbacks
- llm_client.generate_draft_rationale: stub / google / ollama / anthropic cascade + prompt builder
- tasks.build_assignment_draft: ready path, failure path, already-approved no-op
- API: list / retrieve / generate / approve / dismiss with teacher-only permissions
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"ad_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


def make_chapter(db, subject, standard, name):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.get_or_create(name=name, subject=subject, standard=standard)[0]


def make_question(db, standard, subject, chapter, difficulty=2):
    from openshiksha.apps.core.models import Question, QuestionSubpart, QuestionType

    q = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=difficulty,
    )
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        question_text=f"Question for {chapter.name} (d{difficulty})?",
        options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
        correct_answer={"type": "mcq", "answer": "B"},
    )
    return q


def make_tick(db, student, question, subject_room, mark=1.0):
    from openshiksha.apps.core.models import QuestionSubpart
    from openshiksha.apps.edge.models import Tick

    subpart = QuestionSubpart.objects.filter(question=question).first()
    return Tick.objects.create(
        student=student,
        question_subpart=subpart,
        submission=None,
        subject_room=subject_room,
        mark=mark,
    )


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="AD Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="ad_teacher")
    other_teacher = make_user(db, role="teacher", username="ad_other_teacher")
    s1 = make_user(db, role="student", username="ad_s1")
    s2 = make_user(db, role="student", username="ad_s2")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    classroom.students.add(s1, s2)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(s1, s2)

    weak_chapter = make_chapter(db, subject, standard, "Long Division")
    strong_chapter = make_chapter(db, subject, standard, "Fractions")
    # A small bank: several questions per chapter across difficulties.
    weak_qs = [make_question(db, standard, subject, weak_chapter, difficulty=d) for d in (1, 2, 3, 4)]
    strong_qs = [make_question(db, standard, subject, strong_chapter, difficulty=d) for d in (2, 3)]

    return {
        "school": school,
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "students": [s1, s2],
        "classroom": classroom,
        "subject_room": subject_room,
        "weak_chapter": weak_chapter,
        "strong_chapter": strong_chapter,
        "weak_qs": weak_qs,
        "strong_qs": strong_qs,
    }


def seed_weakness(setup):
    """Record low scores on the weak chapter and high scores on the strong one."""
    for q in setup["weak_qs"]:
        make_tick(setup, setup["students"][0], q, setup["subject_room"], mark=0.1)
        make_tick(setup, setup["students"][1], q, setup["subject_room"], mark=0.2)
    for q in setup["strong_qs"]:
        make_tick(setup, setup["students"][0], q, setup["subject_room"], mark=0.9)
        make_tick(setup, setup["students"][1], q, setup["subject_room"], mark=1.0)


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_draft_create_and_properties(setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.READY,
        selected_questions=[{"question_id": 1}, {"question_id": 2}],
    )
    assert draft.question_count == 2
    assert draft.is_actionable is True
    assert "AssignmentDraft" in str(draft)


@pytest.mark.django_db
def test_draft_not_actionable_when_pending(setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.PENDING,
    )
    assert draft.is_actionable is False
    assert draft.question_count == 0


# ─────────────────────────────────────────────────────────────
# Analytics tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_rank_weak_chapters_orders_weakest_first(setup):
    from openshiksha.apps.ai.analytics import rank_weak_chapters_for_room

    seed_weakness(setup)
    ranked = rank_weak_chapters_for_room(setup["subject_room"])

    assert ranked
    assert ranked[0]["chapter_name"] == "Long Division"
    assert ranked[0]["avg_score"] < 0.5


@pytest.mark.django_db
def test_rank_weak_chapters_empty_without_data(setup):
    from openshiksha.apps.ai.analytics import rank_weak_chapters_for_room

    assert rank_weak_chapters_for_room(setup["subject_room"]) == []


@pytest.mark.django_db
def test_rank_weak_chapters_falls_back_when_no_struggle(setup):
    """When nothing is below threshold, the weakest chapters are still returned."""
    from openshiksha.apps.ai.analytics import rank_weak_chapters_for_room

    for q in setup["weak_qs"]:
        make_tick(setup, setup["students"][0], q, setup["subject_room"], mark=0.7)
        make_tick(setup, setup["students"][1], q, setup["subject_room"], mark=0.8)

    ranked = rank_weak_chapters_for_room(setup["subject_room"])
    assert ranked
    assert ranked[0]["chapter_name"] == "Long Division"


@pytest.mark.django_db
def test_build_draft_selects_questions(setup):
    from openshiksha.apps.ai.analytics import build_assignment_draft

    seed_weakness(setup)
    result = build_assignment_draft(setup["subject_room"], size=4, target_difficulty=2)

    assert result["error"] is None
    assert len(result["selected_questions"]) == 4
    assert result["estimated_minutes"] > 0
    assert result["title"]
    # Every chosen item carries a reason and a known question id.
    for item in result["selected_questions"]:
        assert item["reason"]
        assert "estimated_minutes" not in item  # popped before returning
    # Weakest chapter should dominate the selection.
    chapter_names = {item["chapter_name"] for item in result["selected_questions"]}
    assert "Long Division" in chapter_names


@pytest.mark.django_db
def test_build_draft_prefers_target_difficulty(setup):
    from openshiksha.apps.ai.analytics import build_assignment_draft

    seed_weakness(setup)
    # Only the weak chapter is below threshold; ask for difficulty 4.
    result = build_assignment_draft(setup["subject_room"], size=1, target_difficulty=4)
    assert result["error"] is None
    assert result["selected_questions"][0]["difficulty"] == 4


@pytest.mark.django_db
def test_build_draft_excludes_recently_assigned(setup):
    from openshiksha.apps.ai.analytics import build_assignment_draft
    from openshiksha.apps.core.models import Assignment, ProblemSet

    seed_weakness(setup)
    # Assign a problem set containing two of the weak-chapter questions to the room.
    ps = ProblemSet.objects.create(
        school=setup["school"],
        standard=setup["standard"],
        subject=setup["subject"],
        chapter=setup["weak_chapter"],
        title="Already used",
        number=99,
    )
    used = setup["weak_qs"][:2]
    ps.questions.set(used)
    Assignment.objects.create(
        subject_room=setup["subject_room"],
        problem_set=ps,
        assigned_by=setup["teacher"],
        due_at=timezone.now() + timedelta(days=3),
    )

    result = build_assignment_draft(setup["subject_room"], size=8, target_difficulty=2)
    chosen_ids = {item["question_id"] for item in result["selected_questions"]}
    assert chosen_ids.isdisjoint({q.pk for q in used})


@pytest.mark.django_db
def test_build_draft_error_without_weakness(setup):
    from openshiksha.apps.ai.analytics import build_assignment_draft

    result = build_assignment_draft(setup["subject_room"], size=4)
    assert result["error"] is not None
    assert result["selected_questions"] == []


@pytest.mark.django_db
def test_build_draft_error_when_no_fresh_questions(setup):
    """Weak chapter identified, but all its questions are recently assigned."""
    from openshiksha.apps.ai.analytics import build_assignment_draft
    from openshiksha.apps.core.models import Assignment, ProblemSet

    # Make ONLY the weak chapter struggle (strong chapter untouched so it isn't a target).
    for q in setup["weak_qs"]:
        make_tick(setup, setup["students"][0], q, setup["subject_room"], mark=0.1)
        make_tick(setup, setup["students"][1], q, setup["subject_room"], mark=0.2)

    ps = ProblemSet.objects.create(
        school=setup["school"],
        standard=setup["standard"],
        subject=setup["subject"],
        chapter=setup["weak_chapter"],
        title="Uses everything",
        number=99,
    )
    ps.questions.set(setup["weak_qs"])
    Assignment.objects.create(
        subject_room=setup["subject_room"],
        problem_set=ps,
        assigned_by=setup["teacher"],
        due_at=timezone.now() + timedelta(days=3),
    )

    result = build_assignment_draft(setup["subject_room"], size=4)
    assert result["error"] is not None
    assert result["selected_questions"] == []


def test_allocate_per_chapter():
    from openshiksha.apps.ai.analytics import _allocate_per_chapter

    assert _allocate_per_chapter(0, 5) == []
    assert _allocate_per_chapter(2, 8) == [4, 4]
    # Remainder goes to the weakest (first) chapter.
    assert _allocate_per_chapter(3, 8) == [3, 3, 2]


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────

_CHAPTERS = [{"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.3, "tick_count": 8}]


def test_build_draft_rationale_prompt_contains_chapter():
    from openshiksha.apps.ai.llm_client import _build_draft_rationale_prompt

    prompt = _build_draft_rationale_prompt("Mathematics", 8, _CHAPTERS, 6)
    assert "Long Division" in prompt
    assert "Standard 8 Mathematics" in prompt
    assert "6 questions" in prompt


def test_build_draft_rationale_prompt_handles_empty():
    from openshiksha.apps.ai.llm_client import _build_draft_rationale_prompt

    prompt = _build_draft_rationale_prompt("Science", 6, [], 4)
    assert "none identified" in prompt


def test_stub_draft_rationale_mentions_chapter():
    from openshiksha.apps.ai.llm_client import _stub_draft_rationale

    assert "Long Division" in _stub_draft_rationale(_CHAPTERS, 6)
    assert "ready for your review" in _stub_draft_rationale([], 6)


def test_generate_draft_rationale_stub(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")
    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_draft_rationale("Mathematics", 8, _CHAPTERS, 6)
    assert result["model"] == "stub"
    assert "Long Division" in result["text"]


def test_generate_draft_rationale_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    mock_result = {"text": "Claude note.", "model": "claude-sonnet-4-6", "input_tokens": 80, "output_tokens": 40}
    with patch("openshiksha.apps.ai.llm_client._call_anthropic_text", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_draft_rationale("Mathematics", 8, _CHAPTERS, 6)
    mock_call.assert_called_once()
    assert result["model"] == "claude-sonnet-4-6"


def test_generate_draft_rationale_google(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "fake-google")
    mock_result = {"text": "Gemma note.", "model": "gemini-2.5-flash", "input_tokens": 70, "output_tokens": 30}
    with patch("openshiksha.apps.ai.llm_client._call_google_ai_studio", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_draft_rationale("Mathematics", 8, _CHAPTERS, 6)
    mock_call.assert_called_once()
    assert result["model"] == "gemini-2.5-flash"


def test_generate_draft_rationale_ollama(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")
    mock_result = {"text": "Ollama note.", "model": "ollama/gemma3:4b", "input_tokens": 20, "output_tokens": 10}
    with (
        patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=True),
        patch("openshiksha.apps.ai.llm_client._call_ollama", return_value=mock_result) as mock_call,
    ):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_draft_rationale("Mathematics", 8, _CHAPTERS, 6)
    mock_call.assert_called_once()
    assert "ollama" in result["model"]


# ─────────────────────────────────────────────────────────────
# Task tests
# ─────────────────────────────────────────────────────────────

MOCK_RATIONALE = {
    "text": "This draft targets Long Division.",
    "model": "claude-sonnet-4-6",
    "input_tokens": 90,
    "output_tokens": 45,
}


@pytest.mark.django_db
def test_build_draft_task_ready(setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus
    from openshiksha.apps.ai.tasks import build_assignment_draft as task

    seed_weakness(setup)
    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        requested_size=4,
        target_difficulty=2,
    )
    with patch("openshiksha.apps.ai.llm_client.generate_draft_rationale", return_value=MOCK_RATIONALE):
        result = task(draft.pk)

    draft.refresh_from_db()
    assert result["status"] == AssignmentDraftStatus.READY
    assert draft.status == AssignmentDraftStatus.READY
    assert draft.question_count == 4
    assert draft.rationale_text == MOCK_RATIONALE["text"]
    assert draft.model_used == "claude-sonnet-4-6"
    assert draft.estimated_minutes > 0


@pytest.mark.django_db
def test_build_draft_task_failure(setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus
    from openshiksha.apps.ai.tasks import build_assignment_draft as task

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        requested_size=4,
    )
    result = task(draft.pk)

    draft.refresh_from_db()
    assert result["status"] == AssignmentDraftStatus.FAILED
    assert draft.status == AssignmentDraftStatus.FAILED
    assert draft.error_detail


@pytest.mark.django_db
def test_build_draft_task_skips_approved(setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus
    from openshiksha.apps.ai.tasks import build_assignment_draft as task

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.APPROVED,
        selected_questions=[{"question_id": 1}],
    )
    result = task(draft.pk)
    assert result["status"] == AssignmentDraftStatus.APPROVED
    draft.refresh_from_db()
    assert draft.status == AssignmentDraftStatus.APPROVED


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


@pytest.fixture
def ready_draft(db, setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    return AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.READY,
        title="Practice: Long Division",
        rationale_text="Focuses on Long Division.",
        target_chapters=[
            {"chapter_id": setup["weak_chapter"].pk, "chapter_name": "Long Division", "avg_score": 0.2, "tick_count": 8}
        ],
        selected_questions=[
            {
                "question_id": setup["weak_qs"][0].pk,
                "chapter_id": setup["weak_chapter"].pk,
                "chapter_name": "Long Division",
                "difficulty": 1,
                "question_type": "mcq",
                "preview": "Q?",
                "reason": "Targets Long Division.",
            },
            {
                "question_id": setup["weak_qs"][1].pk,
                "chapter_id": setup["weak_chapter"].pk,
                "chapter_name": "Long Division",
                "difficulty": 2,
                "question_type": "mcq",
                "preview": "Q?",
                "reason": "Targets Long Division.",
            },
        ],
        estimated_minutes=6,
    )


@pytest.mark.django_db
def test_api_list_drafts_teacher(api_client, setup, ready_draft):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/assignment-drafts/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["question_count"] == 2


@pytest.mark.django_db
def test_api_list_drafts_filter_by_status(api_client, setup, ready_draft):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/assignment-drafts/?status=ready")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    resp2 = api_client.get("/api/v1/ai/assignment-drafts/?status=approved")
    assert len(resp2.data["results"]) == 0


@pytest.mark.django_db
def test_api_other_teacher_sees_no_drafts(api_client, setup, ready_draft):
    auth(api_client, setup["other_teacher"])
    resp = api_client.get("/api/v1/ai/assignment-drafts/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_student_sees_no_drafts(api_client, setup, ready_draft):
    auth(api_client, setup["students"][0])
    resp = api_client.get("/api/v1/ai/assignment-drafts/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_retrieve_draft(api_client, setup, ready_draft):
    auth(api_client, setup["teacher"])
    resp = api_client.get(f"/api/v1/ai/assignment-drafts/{ready_draft.pk}/")
    assert resp.status_code == 200
    assert resp.data["is_actionable"] is True


@pytest.mark.django_db
def test_api_generate_creates_pending_and_queues(api_client, setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.build_assignment_draft") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/assignment-drafts/generate/",
            {"subject_room_id": setup["subject_room"].pk, "size": 6, "target_difficulty": 3},
            format="json",
        )
    assert resp.status_code == 202
    assert resp.data["status"] == AssignmentDraftStatus.PENDING
    draft = AssignmentDraft.objects.get(pk=resp.data["id"])
    assert draft.requested_size == 6
    assert draft.target_difficulty == 3
    mock_task.delay.assert_called_once_with(draft.pk)


@pytest.mark.django_db
def test_api_generate_not_owner_forbidden(api_client, setup):
    auth(api_client, setup["other_teacher"])
    resp = api_client.post(
        "/api/v1/ai/assignment-drafts/generate/",
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_generate_student_forbidden(api_client, setup):
    auth(api_client, setup["students"][0])
    resp = api_client.post(
        "/api/v1/ai/assignment-drafts/generate/",
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_approve_materialises_assignment(api_client, setup, ready_draft):
    from openshiksha.apps.ai.models import AssignmentDraftStatus
    from openshiksha.apps.core.models import Assignment, ProblemSet

    auth(api_client, setup["teacher"])
    due = (timezone.now() + timedelta(days=5)).isoformat()
    resp = api_client.post(
        f"/api/v1/ai/assignment-drafts/{ready_draft.pk}/approve/",
        {"due_at": due},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["status"] == AssignmentDraftStatus.APPROVED
    assert resp.data["approved_assignment"] is not None

    ready_draft.refresh_from_db()
    ps = ProblemSet.objects.get(pk=ready_draft.approved_problem_set_id)
    assert ps.questions.count() == 2
    assert ps.chapter_id == setup["weak_chapter"].pk
    assignment = Assignment.objects.get(pk=ready_draft.approved_assignment_id)
    assert assignment.subject_room_id == setup["subject_room"].pk


@pytest.mark.django_db
def test_api_approve_custom_title(api_client, setup, ready_draft):
    from openshiksha.apps.core.models import ProblemSet

    auth(api_client, setup["teacher"])
    due = (timezone.now() + timedelta(days=5)).isoformat()
    resp = api_client.post(
        f"/api/v1/ai/assignment-drafts/{ready_draft.pk}/approve/",
        {"due_at": due, "title": "Custom Title"},
        format="json",
    )
    assert resp.status_code == 201
    ready_draft.refresh_from_db()
    ps = ProblemSet.objects.get(pk=ready_draft.approved_problem_set_id)
    assert ps.title == "Custom Title"


@pytest.mark.django_db
def test_api_approve_requires_ready(api_client, setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.PENDING,
    )
    auth(api_client, setup["teacher"])
    resp = api_client.post(
        f"/api/v1/ai/assignment-drafts/{draft.pk}/approve/",
        {"due_at": (timezone.now() + timedelta(days=5)).isoformat()},
        format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_api_approve_other_teacher_404(api_client, setup, ready_draft):
    auth(api_client, setup["other_teacher"])
    resp = api_client.post(
        f"/api/v1/ai/assignment-drafts/{ready_draft.pk}/approve/",
        {"due_at": (timezone.now() + timedelta(days=5)).isoformat()},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_dismiss_draft(api_client, setup, ready_draft):
    from openshiksha.apps.ai.models import AssignmentDraftStatus

    auth(api_client, setup["teacher"])
    resp = api_client.post(f"/api/v1/ai/assignment-drafts/{ready_draft.pk}/dismiss/")
    assert resp.status_code == 200
    assert resp.data["status"] == AssignmentDraftStatus.DISMISSED


@pytest.mark.django_db
def test_api_dismiss_approved_conflict(api_client, setup):
    from openshiksha.apps.ai.models import AssignmentDraft, AssignmentDraftStatus

    draft = AssignmentDraft.objects.create(
        subject_room=setup["subject_room"],
        requested_by=setup["teacher"],
        status=AssignmentDraftStatus.APPROVED,
    )
    auth(api_client, setup["teacher"])
    resp = api_client.post(f"/api/v1/ai/assignment-drafts/{draft.pk}/dismiss/")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_api_unauthenticated_forbidden(api_client):
    resp = api_client.get("/api/v1/ai/assignment-drafts/")
    assert resp.status_code == 401
