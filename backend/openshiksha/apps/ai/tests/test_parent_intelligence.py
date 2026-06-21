"""
Tests for the Parent Intelligence Dashboard feature.

Covers:
- ParentProgressSummary model: creation, unique_together, has_urgent_alert, __str__
- analytics.compute_parent_weekly_stats: empty week, populated week, prev-week delta, inactivity tracking
- analytics.build_home_activities + build_parent_alerts: heuristics for activities/alerts
- llm_client.generate_parent_summary: stub / google / ollama / anthropic cascade + prompt builder
- tasks.generate_parent_progress_summary: default week, idempotency, parent-child validation
- API: list / retrieve / latest / generate with parent-only permissions
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8, first_name="", last_name=""):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"pi_user_{role}_{_user_counter}"
    u = User.objects.create_user(
        username=username, password="pass", role=role, first_name=first_name, last_name=last_name
    )
    if role in ("student", "open_student"):
        u.grade = grade
    u.save()
    return u


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


def make_tick(db, student, subpart, subject_room, mark=1.0, created_at=None):
    from openshiksha.apps.edge.models import Tick

    tick = Tick.objects.create(
        student=student,
        question_subpart=subpart,
        submission=None,
        subject_room=subject_room,
        mark=mark,
    )
    if created_at is not None:
        # auto_now_add prevents directly setting via create; use update
        Tick.objects.filter(pk=tick.pk).update(created_at=created_at)
        tick.refresh_from_db()
    return tick


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="PI Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="pi_teacher")
    parent = make_user(db, role="parent", username="pi_parent")
    other_parent = make_user(db, role="parent", username="pi_other_parent")
    child = make_user(db, role="student", username="pi_child", first_name="Aanya", last_name="Sharma")
    unrelated_child = make_user(db, role="student", username="pi_unrelated_child")
    parent.children.add(child)

    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    classroom.students.add(child)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(child)

    weak_chapter = make_chapter(db, subject, standard, "Long Division")
    strong_chapter = make_chapter(db, subject, standard, "Fractions")
    weak_subpart = make_subpart(db, make_question(db, standard, subject, weak_chapter))
    strong_subpart = make_subpart(db, make_question(db, standard, subject, strong_chapter))

    return {
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "parent": parent,
        "other_parent": other_parent,
        "child": child,
        "unrelated_child": unrelated_child,
        "subject_room": subject_room,
        "weak_chapter": weak_chapter,
        "strong_chapter": strong_chapter,
        "weak_subpart": weak_subpart,
        "strong_subpart": strong_subpart,
    }


def monday_this_week():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_parent_summary_create(setup):
    from openshiksha.apps.ai.models import ParentProgressSummary

    ws = monday_this_week()
    s = ParentProgressSummary.objects.create(
        parent=setup["parent"],
        child=setup["child"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="Aanya did well.",
        ticks_recorded=10,
        active_days=3,
        avg_score=0.7,
        score_delta=0.1,
        alerts=[{"severity": "urgent", "label": "Drop", "detail": "..."}],
    )
    assert s.pk is not None
    assert s.has_urgent_alert is True
    assert "week of" in str(s)


@pytest.mark.django_db
def test_parent_summary_no_urgent_alert(setup):
    from openshiksha.apps.ai.models import ParentProgressSummary

    ws = monday_this_week()
    s = ParentProgressSummary.objects.create(
        parent=setup["parent"],
        child=setup["child"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="OK.",
        alerts=[{"severity": "info", "label": "Nice", "detail": "..."}],
    )
    assert s.has_urgent_alert is False


@pytest.mark.django_db
def test_parent_summary_unique_together(setup):
    from django.db import IntegrityError

    from openshiksha.apps.ai.models import ParentProgressSummary

    ws = monday_this_week()
    ParentProgressSummary.objects.create(
        parent=setup["parent"],
        child=setup["child"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="First.",
    )
    with pytest.raises(IntegrityError):
        ParentProgressSummary.objects.create(
            parent=setup["parent"],
            child=setup["child"],
            week_start=ws,
            week_end=ws + timedelta(days=6),
            summary_text="Duplicate.",
        )


# ─────────────────────────────────────────────────────────────
# Analytics tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_compute_parent_stats_empty_week(setup):
    from openshiksha.apps.ai.analytics import compute_parent_weekly_stats

    past = monday_this_week() - timedelta(days=70)
    stats = compute_parent_weekly_stats(setup["child"], past, past + timedelta(days=6))

    assert stats["ticks_recorded"] == 0
    assert stats["active_days"] == 0
    assert stats["avg_score"] == 0.0
    assert stats["weak_chapters"] == []
    assert stats["strong_chapters"] == []
    assert stats["days_since_last_tick"] is None
    assert stats["child_name"] == "Aanya Sharma"
    assert stats["grade_level"] == 8


@pytest.mark.django_db
def test_compute_parent_stats_with_ticks(setup):
    from openshiksha.apps.ai.analytics import compute_parent_weekly_stats

    make_tick(setup, setup["child"], setup["weak_subpart"], setup["subject_room"], mark=0.1)
    make_tick(setup, setup["child"], setup["weak_subpart"], setup["subject_room"], mark=0.2)
    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=0.9)
    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=1.0)

    ws = monday_this_week()
    stats = compute_parent_weekly_stats(setup["child"], ws, ws + timedelta(days=6))

    assert stats["ticks_recorded"] == 4
    assert stats["active_days"] >= 1
    assert stats["avg_score"] == pytest.approx((0.1 + 0.2 + 0.9 + 1.0) / 4)
    weak_names = [c["chapter_name"] for c in stats["weak_chapters"]]
    strong_names = [c["chapter_name"] for c in stats["strong_chapters"]]
    assert "Long Division" in weak_names
    assert "Fractions" in strong_names
    assert "Mathematics" in stats["subjects_active"]
    assert stats["days_since_last_tick"] == 0


@pytest.mark.django_db
def test_compute_parent_stats_score_delta(setup):
    """Prev-week ticks affect score_delta."""
    from openshiksha.apps.ai.analytics import compute_parent_weekly_stats

    ws = monday_this_week()
    # Prev-week ticks: low scores
    prev_dt = timezone.make_aware(timezone.datetime.combine(ws - timedelta(days=3), timezone.datetime.min.time()))
    make_tick(setup, setup["child"], setup["weak_subpart"], setup["subject_room"], mark=0.2, created_at=prev_dt)
    make_tick(setup, setup["child"], setup["weak_subpart"], setup["subject_room"], mark=0.3, created_at=prev_dt)
    # This-week ticks: high scores
    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=0.9)
    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=1.0)

    stats = compute_parent_weekly_stats(setup["child"], ws, ws + timedelta(days=6))
    assert stats["prev_avg_score"] == pytest.approx(0.25)
    assert stats["avg_score"] == pytest.approx(0.95)
    assert stats["score_delta"] == pytest.approx(0.7)


def test_build_home_activities_uses_weak_chapters():
    from openshiksha.apps.ai.analytics import build_home_activities

    stats = {
        "weak_chapters": [
            {"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.3, "tick_count": 4},
        ],
        "strong_chapters": [],
    }
    activities = build_home_activities(stats)
    assert len(activities) == 1
    assert "Long Division" in activities[0]["title"]


def test_build_home_activities_celebrates_strong_when_no_weak():
    from openshiksha.apps.ai.analytics import build_home_activities

    stats = {
        "weak_chapters": [],
        "strong_chapters": [{"chapter_id": 2, "chapter_name": "Fractions", "avg_score": 0.9, "tick_count": 6}],
    }
    activities = build_home_activities(stats)
    assert len(activities) == 1
    assert "Fractions" in activities[0]["title"]


def test_build_parent_alerts_no_practice():
    from openshiksha.apps.ai.analytics import build_parent_alerts

    stats = {
        "days_since_last_tick": None,
        "score_delta": 0.0,
        "ticks_recorded": 0,
        "weak_chapters": [],
    }
    alerts = build_parent_alerts(stats)
    assert any("No practice" in a["label"] for a in alerts)


def test_build_parent_alerts_inactive_week():
    from openshiksha.apps.ai.analytics import build_parent_alerts

    stats = {
        "days_since_last_tick": 10,
        "score_delta": 0.0,
        "ticks_recorded": 0,
        "weak_chapters": [],
    }
    alerts = build_parent_alerts(stats)
    assert any("Inactive" in a["label"] for a in alerts)


def test_build_parent_alerts_sharp_drop_is_urgent():
    from openshiksha.apps.ai.analytics import build_parent_alerts
    from openshiksha.apps.ai.models import ParentAlertSeverity

    stats = {
        "days_since_last_tick": 1,
        "score_delta": -0.3,
        "ticks_recorded": 10,
        "weak_chapters": [],
    }
    alerts = build_parent_alerts(stats)
    drop = [a for a in alerts if "drop" in a["label"].lower()]
    assert drop and drop[0]["severity"] == ParentAlertSeverity.URGENT


def test_build_parent_alerts_severe_chapter_is_urgent():
    from openshiksha.apps.ai.analytics import build_parent_alerts
    from openshiksha.apps.ai.models import ParentAlertSeverity

    stats = {
        "days_since_last_tick": 1,
        "score_delta": 0.0,
        "ticks_recorded": 10,
        "weak_chapters": [{"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.2, "tick_count": 5}],
    }
    alerts = build_parent_alerts(stats)
    sev = [a for a in alerts if "Struggling" in a["label"]]
    assert sev and sev[0]["severity"] == ParentAlertSeverity.URGENT


def test_build_parent_alerts_improvement_is_info():
    from openshiksha.apps.ai.analytics import build_parent_alerts
    from openshiksha.apps.ai.models import ParentAlertSeverity

    stats = {
        "days_since_last_tick": 1,
        "score_delta": 0.2,
        "ticks_recorded": 10,
        "weak_chapters": [],
    }
    alerts = build_parent_alerts(stats)
    imp = [a for a in alerts if "improvement" in a["label"].lower()]
    assert imp and imp[0]["severity"] == ParentAlertSeverity.INFO


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────


_STATS = {
    "child_name": "Aanya",
    "grade_level": 8,
    "ticks_recorded": 40,
    "active_days": 4,
    "avg_score": 0.72,
    "prev_avg_score": 0.6,
    "score_delta": 0.12,
    "subjects_active": ["Mathematics"],
    "weak_chapters": [{"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.31, "tick_count": 6}],
    "strong_chapters": [{"chapter_id": 2, "chapter_name": "Fractions", "avg_score": 0.88, "tick_count": 8}],
    "days_since_last_tick": 1,
}


def test_build_parent_summary_prompt_mentions_child_and_chapters():
    from openshiksha.apps.ai.llm_client import _build_parent_summary_prompt

    prompt = _build_parent_summary_prompt(_STATS, "en")
    assert "Aanya" in prompt
    assert "Long Division" in prompt
    assert "Fractions" in prompt
    assert "Grade 8" in prompt


def test_build_parent_summary_prompt_hindi_flag():
    from openshiksha.apps.ai.llm_client import _build_parent_summary_prompt

    prompt = _build_parent_summary_prompt(_STATS, "hi")
    assert "Hindi" in prompt


def test_stub_parent_summary_with_ticks():
    from openshiksha.apps.ai.llm_client import _stub_parent_summary

    text = _stub_parent_summary(_STATS)
    assert "Aanya" in text
    assert "Long Division" in text
    assert "Fractions" in text


def test_stub_parent_summary_zero_ticks():
    from openshiksha.apps.ai.llm_client import _stub_parent_summary

    text = _stub_parent_summary({**_STATS, "ticks_recorded": 0, "active_days": 0})
    assert "did not practise" in text


def test_generate_parent_summary_stub(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_parent_summary(_STATS)

    assert result["model"] == "stub"
    assert "Aanya" in result["text"]


def test_generate_parent_summary_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    mock_result = {"text": "Claude parent note.", "model": "claude-sonnet-4-6", "input_tokens": 90, "output_tokens": 40}

    with patch("openshiksha.apps.ai.llm_client._call_anthropic_text", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_parent_summary(_STATS)

    mock_call.assert_called_once()
    assert result["model"] == "claude-sonnet-4-6"


def test_generate_parent_summary_google(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "fake")
    mock_result = {"text": "Gemma parent note.", "model": "gemini-2.5-flash", "input_tokens": 70, "output_tokens": 30}

    with patch("openshiksha.apps.ai.llm_client._call_google_ai_studio", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_parent_summary(_STATS)

    mock_call.assert_called_once()
    assert result["model"] == "gemini-2.5-flash"


def test_generate_parent_summary_ollama(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")
    mock_result = {"text": "Ollama parent note.", "model": "ollama/gemma3:4b", "input_tokens": 20, "output_tokens": 10}

    with (
        patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=True),
        patch("openshiksha.apps.ai.llm_client._call_ollama", return_value=mock_result) as mock_call,
    ):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_parent_summary(_STATS)

    mock_call.assert_called_once()
    assert "ollama" in result["model"]


# ─────────────────────────────────────────────────────────────
# Task tests
# ─────────────────────────────────────────────────────────────


MOCK_SUMMARY = {
    "text": "Aanya is making steady progress this week.",
    "model": "claude-sonnet-4-6",
    "input_tokens": 80,
    "output_tokens": 40,
}


@pytest.mark.django_db
def test_generate_parent_summary_task_default_week(setup):
    from openshiksha.apps.ai.models import ParentProgressSummary
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=0.9)
    make_tick(setup, setup["child"], setup["strong_subpart"], setup["subject_room"], mark=1.0)

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        result = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk)

    summary = ParentProgressSummary.objects.get(pk=result["summary_id"])
    assert summary.week_start == monday_this_week()
    assert summary.week_end == monday_this_week() + timedelta(days=6)
    assert summary.ticks_recorded == 2
    assert summary.summary_text == MOCK_SUMMARY["text"]
    assert summary.model_used == "claude-sonnet-4-6"


@pytest.mark.django_db
def test_generate_parent_summary_task_idempotent(setup):
    from openshiksha.apps.ai.models import ParentProgressSummary
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        r1 = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk)
        r2 = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk)

    assert r1["summary_id"] == r2["summary_id"]
    assert ParentProgressSummary.objects.filter(parent=setup["parent"], child=setup["child"]).count() == 1


@pytest.mark.django_db
def test_generate_parent_summary_task_rejects_unrelated_child(setup):
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        with pytest.raises(ValueError):
            generate_parent_progress_summary(setup["parent"].pk, setup["unrelated_child"].pk)


@pytest.mark.django_db
def test_generate_parent_summary_task_explicit_week_snaps_to_monday(setup):
    from openshiksha.apps.ai.models import ParentProgressSummary
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        result = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk, week_start_iso="2026-05-27")

    summary = ParentProgressSummary.objects.get(pk=result["summary_id"])
    assert summary.week_start.isoformat() == "2026-05-25"


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
def summary(db, setup):
    from openshiksha.apps.ai.models import ParentProgressSummary

    ws = monday_this_week()
    return ParentProgressSummary.objects.create(
        parent=setup["parent"],
        child=setup["child"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="Aanya did well this week.",
        ticks_recorded=12,
        active_days=3,
        avg_score=0.65,
        score_delta=0.05,
        model_used="stub",
    )


@pytest.mark.django_db
def test_api_list_summaries_parent(api_client, setup, summary):
    auth(api_client, setup["parent"])
    resp = api_client.get("/api/v1/ai/parent-summaries/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["summary_text"] == "Aanya did well this week."
    assert resp.data["results"][0]["child_name"] == "Aanya Sharma"


@pytest.mark.django_db
def test_api_list_summaries_filter_by_child(api_client, setup, summary):
    auth(api_client, setup["parent"])
    resp = api_client.get(f"/api/v1/ai/parent-summaries/?child={setup['child'].pk}")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_other_parent_sees_nothing(api_client, setup, summary):
    auth(api_client, setup["other_parent"])
    resp = api_client.get("/api/v1/ai/parent-summaries/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_student_cannot_list(api_client, setup, summary):
    auth(api_client, setup["child"])
    resp = api_client.get("/api/v1/ai/parent-summaries/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_retrieve_summary(api_client, setup, summary):
    auth(api_client, setup["parent"])
    resp = api_client.get(f"/api/v1/ai/parent-summaries/{summary.pk}/")
    assert resp.status_code == 200
    assert resp.data["avg_score"] == pytest.approx(0.65)


@pytest.mark.django_db
def test_api_latest_summary(api_client, setup, summary):
    auth(api_client, setup["parent"])
    resp = api_client.get(f"/api/v1/ai/parent-summaries/latest/?child={setup['child'].pk}")
    assert resp.status_code == 200
    assert resp.data["id"] == summary.pk


@pytest.mark.django_db
def test_api_latest_requires_child(api_client, setup, summary):
    auth(api_client, setup["parent"])
    resp = api_client.get("/api/v1/ai/parent-summaries/latest/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_latest_404_when_none(api_client, setup):
    auth(api_client, setup["parent"])
    resp = api_client.get(f"/api/v1/ai/parent-summaries/latest/?child={setup['child'].pk}")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_latest_student_forbidden(api_client, setup, summary):
    auth(api_client, setup["child"])
    resp = api_client.get(f"/api/v1/ai/parent-summaries/latest/?child={setup['child'].pk}")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_generate_summary_queues_task(api_client, setup):
    auth(api_client, setup["parent"])
    with patch("openshiksha.apps.ai.views.generate_parent_progress_summary") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/parent-summaries/generate/",
            {"child_id": setup["child"].pk},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(setup["parent"].pk, setup["child"].pk, None, "en")


@pytest.mark.django_db
def test_api_generate_summary_with_week_and_language(api_client, setup):
    auth(api_client, setup["parent"])
    with patch("openshiksha.apps.ai.views.generate_parent_progress_summary") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/parent-summaries/generate/",
            {"child_id": setup["child"].pk, "week_start": "2026-05-25", "language": "hi"},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(setup["parent"].pk, setup["child"].pk, "2026-05-25", "hi")


@pytest.mark.django_db
def test_api_generate_summary_unrelated_child_forbidden(api_client, setup):
    auth(api_client, setup["parent"])
    resp = api_client.post(
        "/api/v1/ai/parent-summaries/generate/",
        {"child_id": setup["unrelated_child"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_generate_summary_student_forbidden(api_client, setup):
    auth(api_client, setup["child"])
    resp = api_client.post(
        "/api/v1/ai/parent-summaries/generate/",
        {"child_id": setup["child"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_unauthenticated_forbidden(api_client):
    resp = api_client.get("/api/v1/ai/parent-summaries/")
    assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────
# Weekly email digest + Monday batch
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_notify_parent_weekly_summary_sends(setup, summary):
    from openshiksha.apps.ai.emails import notify_parent_weekly_summary

    parent = setup["parent"]
    parent.email = "parent@example.com"
    parent.save()
    summary.alerts = [{"severity": "urgent", "label": "Sharp drop", "detail": "Down 20% vs last week."}]
    summary.home_activities = [{"title": "Practise Long Division together", "description": "15 minutes."}]
    summary.save()

    with patch("openshiksha.apps.ai.emails.send_mail") as mock_send:
        sent = notify_parent_weekly_summary(parent, setup["child"], summary)

    assert sent is True
    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["recipient_list"] == ["parent@example.com"]
    assert "Aanya" in kwargs["subject"]
    # Narrative, the urgent alert, and the home activity all appear in the body.
    assert "Aanya did well this week." in kwargs["message"]
    assert "Sharp drop" in kwargs["message"]
    assert "Practise Long Division together" in kwargs["message"]


@pytest.mark.django_db
def test_notify_parent_weekly_summary_skips_without_email(setup, summary):
    from openshiksha.apps.ai.emails import notify_parent_weekly_summary

    setup["parent"].email = ""
    setup["parent"].save()

    with patch("openshiksha.apps.ai.emails.send_mail") as mock_send:
        sent = notify_parent_weekly_summary(setup["parent"], setup["child"], summary)

    assert sent is False
    mock_send.assert_not_called()


@pytest.mark.django_db
def test_notify_parent_weekly_summary_swallows_smtp_error(setup, summary):
    from openshiksha.apps.ai.emails import notify_parent_weekly_summary

    setup["parent"].email = "parent@example.com"
    setup["parent"].save()

    with patch("openshiksha.apps.ai.emails.send_mail", side_effect=Exception("SMTP down")):
        sent = notify_parent_weekly_summary(setup["parent"], setup["child"], summary)

    assert sent is False  # error logged, not raised


@pytest.mark.django_db
def test_generate_parent_summary_task_sends_email_when_requested(setup):
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    setup["parent"].email = "parent@example.com"
    setup["parent"].save()

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        with patch("openshiksha.apps.ai.emails.send_mail") as mock_send:
            result = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk, send_email=True)

    assert result["emailed"] is True
    mock_send.assert_called_once()


@pytest.mark.django_db
def test_generate_parent_summary_task_no_email_by_default(setup):
    from openshiksha.apps.ai.tasks import generate_parent_progress_summary

    setup["parent"].email = "parent@example.com"
    setup["parent"].save()

    with patch("openshiksha.apps.ai.llm_client.generate_parent_summary", return_value=MOCK_SUMMARY):
        with patch("openshiksha.apps.ai.emails.send_mail") as mock_send:
            result = generate_parent_progress_summary(setup["parent"].pk, setup["child"].pk)

    assert result["emailed"] is False
    mock_send.assert_not_called()


@pytest.mark.django_db
def test_enqueue_weekly_parent_summaries_fans_out_per_pair(setup):
    from openshiksha.apps.ai.tasks import enqueue_weekly_parent_summaries

    expected_week = (monday_this_week() - timedelta(days=7)).isoformat()

    with patch("openshiksha.apps.ai.tasks.generate_parent_progress_summary.delay") as mock_delay:
        result = enqueue_weekly_parent_summaries()

    # The fixture links exactly one (parent, child) pair; other_parent has no children.
    assert result["pairs"] == 1
    assert result["enqueued"] == 1
    assert result["week_start"] == expected_week
    mock_delay.assert_called_once_with(
        setup["parent"].pk,
        setup["child"].pk,
        week_start_iso=expected_week,
        language="en",
        send_email=True,
    )


@pytest.mark.django_db
def test_enqueue_weekly_parent_summaries_passes_parent_language(setup):
    """LA-7: a Hindi-preferring parent gets a Hindi AI summary from the Monday batch."""
    from openshiksha.apps.ai.tasks import enqueue_weekly_parent_summaries

    setup["parent"].preferred_language = "hi"
    setup["parent"].save()

    with patch("openshiksha.apps.ai.tasks.generate_parent_progress_summary.delay") as mock_delay:
        enqueue_weekly_parent_summaries()

    assert mock_delay.call_args.kwargs["language"] == "hi"


@pytest.mark.django_db
def test_notify_parent_weekly_summary_renders_hindi_chrome(setup, summary, settings):
    """LA-7: email chrome follows parent.preferred_language; the AI narrative
    text is embedded as stored (already language-aware via the generate task)."""
    from django.core import mail

    from openshiksha.apps.ai.emails import notify_parent_weekly_summary

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    setup["parent"].email = "parent@example.com"
    setup["parent"].preferred_language = "hi"
    setup["parent"].save()

    sent = notify_parent_weekly_summary(setup["parent"], setup["child"], summary)

    assert sent is True
    assert len(mail.outbox) == 1
    assert "साप्ताहिक लर्निंग समरी" in mail.outbox[0].subject
    assert "Aanya" in mail.outbox[0].subject
    body = mail.outbox[0].body
    assert "नमस्ते" in body
    assert "इनसाइट्स खोलें" in body
    # The stored narrative passes through verbatim.
    assert "Aanya did well this week." in body


@pytest.mark.django_db
def test_notify_parent_weekly_summary_english_default(setup, summary, settings):
    from django.core import mail

    from openshiksha.apps.ai.emails import notify_parent_weekly_summary

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    setup["parent"].email = "parent@example.com"
    setup["parent"].save()

    sent = notify_parent_weekly_summary(setup["parent"], setup["child"], summary)

    assert sent is True
    assert "weekly learning summary" in mail.outbox[0].subject
    assert "Hi " in mail.outbox[0].body


@pytest.mark.django_db
def test_enqueue_weekly_parent_summaries_snaps_explicit_week_to_monday(setup):
    from openshiksha.apps.ai.tasks import enqueue_weekly_parent_summaries

    with patch("openshiksha.apps.ai.tasks.generate_parent_progress_summary.delay") as mock_delay:
        result = enqueue_weekly_parent_summaries(week_start_iso="2026-05-27")  # a Wednesday

    assert result["week_start"] == "2026-05-25"  # snapped back to Monday
    assert mock_delay.call_args.kwargs["week_start_iso"] == "2026-05-25"
