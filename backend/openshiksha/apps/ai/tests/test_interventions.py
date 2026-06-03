"""
Tests for the Teacher AI Assistant — Intervention Suggestions feature.

Covers:
- InterventionSuggestion model: creation, unique_together, priority_for, __str__
- analytics.compute_interventions_for_subject_room: empty, gaps grouped per student,
  misconception labels, focus-chapter ordering, priority/severity derivation
- llm_client.generate_intervention_plan: stub / anthropic cascade + prompt builder
- tasks.generate_interventions_for_subject_room: generation, idempotency, auto-resolve,
  preservation of teacher decisions
- API: list / retrieve / filter / generate / set-status with teacher-only permissions
"""

from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"iv_user_{role}_{_user_counter}"
    return User.objects.create_user(username=username, password="pass", role=role)


def make_chapter(db, subject, standard, name):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.get_or_create(name=name, subject=subject, standard=standard)[0]


def make_question(db, standard, subject, chapter):
    from openshiksha.apps.core.models import Question, QuestionType

    return Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=2,
    )


def make_subpart(db, question, index=0):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(
        question=question,
        index=index,
        question_text="What is 2 + 2?",
        options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
        correct_answer={"type": "mcq", "answer": "B"},
    )


def make_gap(db, student, chapter, subject_room, avg_score, tick_count=5, is_resolved=False):
    from openshiksha.apps.ai.models import LearningGap

    return LearningGap.objects.create(
        student=student,
        chapter=chapter,
        subject_room=subject_room,
        avg_score=avg_score,
        severity=LearningGap.severity_for_score(avg_score),
        tick_count=tick_count,
        is_resolved=is_resolved,
    )


def make_misconception(db, student, subpart, label):
    from openshiksha.apps.ai.models import StudentMisconception

    return StudentMisconception.objects.create(
        student=student,
        question_subpart=subpart,
        submission=None,
        student_answer={"answer": "A"},
        misconception_label=label,
        diagnosis_text="Faulty reasoning.",
        remediation_tip="Review the chapter.",
        grade_level=8,
    )


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="IV Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="iv_teacher")
    other_teacher = make_user(db, role="teacher", username="iv_other_teacher")
    s1 = make_user(db, role="student", username="iv_s1")
    s2 = make_user(db, role="student", username="iv_s2")
    s3 = make_user(db, role="student", username="iv_s3")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    for s in (s1, s2, s3):
        classroom.students.add(s)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    for s in (s1, s2, s3):
        subject_room.students.add(s)

    ch_a = make_chapter(db, subject, standard, "Long Division")
    ch_b = make_chapter(db, subject, standard, "Fractions")
    subpart_a = make_subpart(db, make_question(db, standard, subject, ch_a))

    return {
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "students": [s1, s2, s3],
        "subject_room": subject_room,
        "ch_a": ch_a,
        "ch_b": ch_b,
        "subpart_a": subpart_a,
    }


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_intervention_create_and_str(setup):
    from openshiksha.apps.ai.models import GapSeverity, InterventionStatus, InterventionSuggestion

    obj = InterventionSuggestion.objects.create(
        subject_room=setup["subject_room"],
        student=setup["students"][0],
        severity=GapSeverity.SEVERE,
        priority=5,
        strategy_text="Re-teach long division.",
        avg_score=0.2,
        gap_count=2,
    )
    assert obj.status == InterventionStatus.OPEN
    assert "P5" in str(obj)
    assert "iv_s1" in str(obj)


@pytest.mark.django_db
def test_intervention_unique_per_room_student(setup):
    from django.db import IntegrityError

    from openshiksha.apps.ai.models import GapSeverity, InterventionSuggestion

    InterventionSuggestion.objects.create(
        subject_room=setup["subject_room"],
        student=setup["students"][0],
        severity=GapSeverity.MILD,
        strategy_text="x",
    )
    with pytest.raises(IntegrityError):
        InterventionSuggestion.objects.create(
            subject_room=setup["subject_room"],
            student=setup["students"][0],
            severity=GapSeverity.MILD,
            strategy_text="y",
        )


def test_priority_for_mapping():
    from openshiksha.apps.ai.models import GapSeverity, InterventionSuggestion

    pf = InterventionSuggestion.priority_for
    assert pf(GapSeverity.SEVERE, 1) == 4
    assert pf(GapSeverity.SEVERE, 3) == 5  # capped at 5
    assert pf(GapSeverity.MODERATE, 1) == 3
    assert pf(GapSeverity.MILD, 1) == 2
    assert pf(GapSeverity.MILD, 5) == 5
    # In practice gap_count is always >= 1; the result never drops below the base.
    assert pf(GapSeverity.MILD, 0) == 2


# ─────────────────────────────────────────────────────────────
# analytics tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_compute_interventions_empty(setup):
    from openshiksha.apps.ai.analytics import compute_interventions_for_subject_room

    assert compute_interventions_for_subject_room(setup["subject_room"]) == []


@pytest.mark.django_db
def test_compute_interventions_groups_gaps_per_student(setup):
    from openshiksha.apps.ai.analytics import compute_interventions_for_subject_room

    # Student 0: two gaps (severe + mild) → grouped, severity = worst (severe)
    make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.15)
    make_gap(setup, setup["students"][0], setup["ch_b"], setup["subject_room"], avg_score=0.45)
    # Student 1: one moderate gap
    make_gap(setup, setup["students"][1], setup["ch_a"], setup["subject_room"], avg_score=0.30)
    # Resolved gaps are ignored
    make_gap(setup, setup["students"][2], setup["ch_a"], setup["subject_room"], avg_score=0.30, is_resolved=True)

    snapshots = compute_interventions_for_subject_room(setup["subject_room"])

    assert len(snapshots) == 2  # student 2's only gap is resolved
    s0 = next(s for s in snapshots if s["student_id"] == setup["students"][0].pk)
    assert s0["gap_count"] == 2
    assert s0["severity"] == "severe"
    assert s0["avg_score"] == pytest.approx((0.15 + 0.45) / 2)
    # Focus chapters ordered weakest-first
    assert s0["focus_chapters"][0]["chapter_name"] == "Long Division"
    assert s0["priority"] == 5  # severe + 2 gaps

    # Sorted by priority desc → student 0 (P5) before student 1
    assert snapshots[0]["student_id"] == setup["students"][0].pk


@pytest.mark.django_db
def test_compute_interventions_includes_misconception_labels(setup):
    from openshiksha.apps.ai.analytics import compute_interventions_for_subject_room

    make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.2)
    # Two of the same label + one other → counts and ordering
    make_misconception(setup, setup["students"][0], setup["subpart_a"], "Adds numerators and denominators")
    sp2 = make_subpart(setup, make_question(setup, setup["standard"], setup["subject"], setup["ch_a"]), index=1)
    make_misconception(setup, setup["students"][0], sp2, "Adds numerators and denominators")
    sp3 = make_subpart(setup, make_question(setup, setup["standard"], setup["subject"], setup["ch_a"]), index=2)
    make_misconception(setup, setup["students"][0], sp3, "Forgets to carry")

    snapshots = compute_interventions_for_subject_room(setup["subject_room"])
    labels = snapshots[0]["misconception_labels"]
    assert labels[0]["label"] == "adds numerators and denominators"
    assert labels[0]["count"] == 2
    assert {m["label"] for m in labels} == {"adds numerators and denominators", "forgets to carry"}


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────

_STATS = {
    "student_name": "Asha",
    "grade_level": 8,
    "avg_score": 0.22,
    "gap_count": 2,
    "severity": "severe",
    "focus_chapters": [
        {"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.15, "severity": "severe"},
        {"chapter_id": 2, "chapter_name": "Fractions", "avg_score": 0.45, "severity": "mild"},
    ],
    "misconception_labels": [{"label": "adds numerators and denominators", "count": 3}],
}


def test_build_intervention_prompt_contains_evidence():
    from openshiksha.apps.ai.llm_client import _build_intervention_prompt

    prompt = _build_intervention_prompt(_STATS, "Mathematics", 8)
    assert "Asha" in prompt
    assert "Long Division" in prompt
    assert "adds numerators and denominators" in prompt
    assert "Standard 8 Mathematics" in prompt


def test_stub_intervention_mentions_weakest_chapter():
    from openshiksha.apps.ai.llm_client import _stub_intervention

    text = _stub_intervention(_STATS)
    assert "Long Division" in text
    assert "Asha" in text
    assert "adds numerators and denominators" in text


def test_stub_intervention_handles_no_chapters():
    from openshiksha.apps.ai.llm_client import _stub_intervention

    text = _stub_intervention({"student_name": "Ravi", "focus_chapters": [], "misconception_labels": []})
    assert "Ravi" in text


def test_generate_intervention_plan_stub(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_intervention_plan(_STATS, "Mathematics", 8)

    assert result["model"] == "stub"
    assert result["input_tokens"] == 0
    assert "Long Division" in result["text"]


def test_generate_intervention_plan_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    mock_result = {"text": "Claude plan.", "model": "claude-sonnet-4-6", "input_tokens": 90, "output_tokens": 40}

    with patch("openshiksha.apps.ai.llm_client._call_anthropic_text", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_intervention_plan(_STATS, "Mathematics", 8)

    mock_call.assert_called_once()
    assert result["model"] == "claude-sonnet-4-6"


# ─────────────────────────────────────────────────────────────
# task tests
# ─────────────────────────────────────────────────────────────

MOCK_PLAN = {"text": "Targeted re-teach plan.", "model": "claude-sonnet-4-6", "input_tokens": 80, "output_tokens": 30}


@pytest.mark.django_db
def test_generate_interventions_task_creates_rows(setup):
    from openshiksha.apps.ai.models import InterventionSuggestion
    from openshiksha.apps.ai.tasks import generate_interventions_for_subject_room

    make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.15)
    make_gap(setup, setup["students"][1], setup["ch_a"], setup["subject_room"], avg_score=0.30)

    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        result = generate_interventions_for_subject_room(setup["subject_room"].pk)

    assert result["generated"] == 2
    rows = InterventionSuggestion.objects.filter(subject_room=setup["subject_room"])
    assert rows.count() == 2
    row = rows.get(student=setup["students"][0])
    assert row.strategy_text == "Targeted re-teach plan."
    assert row.model_used == "claude-sonnet-4-6"
    assert row.priority == 4  # severe, 1 gap


@pytest.mark.django_db
def test_generate_interventions_task_idempotent(setup):
    from openshiksha.apps.ai.models import InterventionSuggestion
    from openshiksha.apps.ai.tasks import generate_interventions_for_subject_room

    make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.15)

    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        generate_interventions_for_subject_room(setup["subject_room"].pk)
        generate_interventions_for_subject_room(setup["subject_room"].pk)

    assert InterventionSuggestion.objects.filter(subject_room=setup["subject_room"]).count() == 1


@pytest.mark.django_db
def test_generate_interventions_task_auto_resolves(setup):
    """A student whose gaps closed has their open suggestion auto-resolved on refresh."""
    from openshiksha.apps.ai.models import InterventionStatus, InterventionSuggestion
    from openshiksha.apps.ai.tasks import generate_interventions_for_subject_room

    gap = make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.15)
    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        generate_interventions_for_subject_room(setup["subject_room"].pk)

    # Student recovers — gap resolved
    gap.is_resolved = True
    gap.save(update_fields=["is_resolved"])

    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        result = generate_interventions_for_subject_room(setup["subject_room"].pk)

    assert result["generated"] == 0
    assert result["auto_resolved"] == 1
    obj = InterventionSuggestion.objects.get(subject_room=setup["subject_room"], student=setup["students"][0])
    assert obj.status == InterventionStatus.RESOLVED


@pytest.mark.django_db
def test_generate_interventions_task_preserves_acknowledged(setup):
    """A teacher's acknowledged decision survives a refresh that still finds the gap."""
    from openshiksha.apps.ai.models import InterventionStatus, InterventionSuggestion
    from openshiksha.apps.ai.tasks import generate_interventions_for_subject_room

    make_gap(setup, setup["students"][0], setup["ch_a"], setup["subject_room"], avg_score=0.15)
    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        generate_interventions_for_subject_room(setup["subject_room"].pk)

    obj = InterventionSuggestion.objects.get(subject_room=setup["subject_room"], student=setup["students"][0])
    obj.status = InterventionStatus.ACKNOWLEDGED
    obj.save(update_fields=["status"])

    with patch("openshiksha.apps.ai.llm_client.generate_intervention_plan", return_value=MOCK_PLAN):
        generate_interventions_for_subject_room(setup["subject_room"].pk)

    obj.refresh_from_db()
    assert obj.status == InterventionStatus.ACKNOWLEDGED


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
def suggestion(db, setup):
    from openshiksha.apps.ai.models import GapSeverity, InterventionSuggestion

    return InterventionSuggestion.objects.create(
        subject_room=setup["subject_room"],
        student=setup["students"][0],
        severity=GapSeverity.SEVERE,
        priority=5,
        strategy_text="Re-teach long division first.",
        avg_score=0.2,
        gap_count=2,
        focus_chapters=[{"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.2, "severity": "severe"}],
    )


@pytest.mark.django_db
def test_api_list_interventions_teacher(api_client, setup, suggestion):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/interventions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    row = resp.data["results"][0]
    assert row["strategy_text"] == "Re-teach long division first."
    assert row["student_name"]
    assert row["focus_chapters"][0]["chapter_name"] == "Long Division"


@pytest.mark.django_db
def test_api_list_filter_by_status(api_client, setup, suggestion):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/interventions/?status=open")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    resp = api_client.get("/api/v1/ai/interventions/?status=resolved")
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_other_teacher_sees_nothing(api_client, setup, suggestion):
    auth(api_client, setup["other_teacher"])
    resp = api_client.get("/api/v1/ai/interventions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_student_sees_nothing(api_client, setup, suggestion):
    auth(api_client, setup["students"][0])
    resp = api_client.get("/api/v1/ai/interventions/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_generate_queues_task(api_client, setup):
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.generate_interventions_for_subject_room") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/interventions/generate/",
            {"subject_room_id": setup["subject_room"].pk},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(setup["subject_room"].pk)


@pytest.mark.django_db
def test_api_generate_forbidden_for_other_teacher(api_client, setup):
    auth(api_client, setup["other_teacher"])
    resp = api_client.post(
        "/api/v1/ai/interventions/generate/",
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_set_status_acknowledge(api_client, setup, suggestion):
    from openshiksha.apps.ai.models import InterventionStatus

    auth(api_client, setup["teacher"])
    resp = api_client.post(
        f"/api/v1/ai/interventions/{suggestion.pk}/set-status/",
        {"status": "acknowledged"},
        format="json",
    )
    assert resp.status_code == 200
    suggestion.refresh_from_db()
    assert suggestion.status == InterventionStatus.ACKNOWLEDGED
    assert suggestion.acknowledged_by_id == setup["teacher"].pk
    assert suggestion.acknowledged_at is not None


@pytest.mark.django_db
def test_api_set_status_dismiss(api_client, setup, suggestion):
    from openshiksha.apps.ai.models import InterventionStatus

    auth(api_client, setup["teacher"])
    resp = api_client.post(
        f"/api/v1/ai/interventions/{suggestion.pk}/set-status/",
        {"status": "dismissed"},
        format="json",
    )
    assert resp.status_code == 200
    suggestion.refresh_from_db()
    assert suggestion.status == InterventionStatus.DISMISSED


@pytest.mark.django_db
def test_api_set_status_rejects_invalid(api_client, setup, suggestion):
    auth(api_client, setup["teacher"])
    resp = api_client.post(
        f"/api/v1/ai/interventions/{suggestion.pk}/set-status/",
        {"status": "open"},  # not an allowed transition target
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_other_teacher_cannot_set_status(api_client, setup, suggestion):
    auth(api_client, setup["other_teacher"])
    resp = api_client.post(
        f"/api/v1/ai/interventions/{suggestion.pk}/set-status/",
        {"status": "dismissed"},
        format="json",
    )
    assert resp.status_code == 404  # not in their queryset
