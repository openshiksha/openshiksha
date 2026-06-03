"""
Tests for the Teacher AI Assistant — Weekly Class Summary Reports feature.

Covers:
- WeeklyClassReport model: creation, unique_together, participation_rate, __str__
- analytics.compute_weekly_class_stats: empty window, populated window, chapter highlights
- llm_client.generate_class_summary: stub / google / ollama / anthropic cascade + prompt builder
- tasks.generate_weekly_class_report: default week, explicit week, idempotency
- API: list / retrieve / latest / generate with teacher-only permissions
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"wr_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
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


def make_tick(db, student, subpart, subject_room, mark=1.0):
    from openshiksha.apps.edge.models import Tick

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
    school = School.objects.get_or_create(name="WR Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="wr_teacher")
    other_teacher = make_user(db, role="teacher", username="wr_other_teacher")
    s1 = make_user(db, role="student", username="wr_s1")
    s2 = make_user(db, role="student", username="wr_s2")
    s3 = make_user(db, role="student", username="wr_s3")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    for s in (s1, s2, s3):
        classroom.students.add(s)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    for s in (s1, s2, s3):
        subject_room.students.add(s)

    weak_chapter = make_chapter(db, subject, standard, "Long Division")
    strong_chapter = make_chapter(db, subject, standard, "Fractions")
    weak_subpart = make_subpart(db, make_question(db, standard, subject, weak_chapter))
    strong_subpart = make_subpart(db, make_question(db, standard, subject, strong_chapter))

    return {
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "students": [s1, s2, s3],
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
def test_weekly_report_create(setup):
    from openshiksha.apps.ai.models import WeeklyClassReport

    ws = monday_this_week()
    report = WeeklyClassReport.objects.create(
        subject_room=setup["subject_room"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="The class did well this week.",
        total_students=3,
        active_students=2,
        ticks_recorded=10,
        class_avg_score=0.7,
        struggling_chapters=[{"chapter_id": 1, "chapter_name": "X", "avg_score": 0.3, "tick_count": 4}],
        strong_chapters=[],
        model_used="stub",
    )
    assert report.pk is not None
    assert report.participation_rate == pytest.approx(2 / 3)
    assert "class did well" in report.summary_text
    assert "week of" in str(report)


@pytest.mark.django_db
def test_weekly_report_participation_rate_zero_students(setup):
    from openshiksha.apps.ai.models import WeeklyClassReport

    ws = monday_this_week()
    report = WeeklyClassReport.objects.create(
        subject_room=setup["subject_room"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="No students.",
        total_students=0,
        active_students=0,
    )
    assert report.participation_rate == 0.0


@pytest.mark.django_db
def test_weekly_report_unique_together(setup):
    from django.db import IntegrityError

    from openshiksha.apps.ai.models import WeeklyClassReport

    ws = monday_this_week()
    WeeklyClassReport.objects.create(
        subject_room=setup["subject_room"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="First.",
    )
    with pytest.raises(IntegrityError):
        WeeklyClassReport.objects.create(
            subject_room=setup["subject_room"],
            week_start=ws,
            week_end=ws + timedelta(days=6),
            summary_text="Duplicate.",
        )


# ─────────────────────────────────────────────────────────────
# Analytics tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_compute_weekly_stats_empty_window(setup):
    """A past week with no ticks yields a zeroed snapshot."""
    from openshiksha.apps.ai.analytics import compute_weekly_class_stats

    past_start = monday_this_week() - timedelta(days=70)
    stats = compute_weekly_class_stats(setup["subject_room"], past_start, past_start + timedelta(days=6))

    assert stats["total_students"] == 3
    assert stats["active_students"] == 0
    assert stats["ticks_recorded"] == 0
    assert stats["class_avg_score"] == 0.0
    assert stats["struggling_chapters"] == []
    assert stats["strong_chapters"] == []


@pytest.mark.django_db
def test_compute_weekly_stats_with_ticks(setup):
    """Ticks recorded this week populate participation, average, and chapter highlights."""
    from openshiksha.apps.ai.analytics import compute_weekly_class_stats

    # Weak chapter: two students score low → struggling
    make_tick(setup, setup["students"][0], setup["weak_subpart"], setup["subject_room"], mark=0.1)
    make_tick(setup, setup["students"][1], setup["weak_subpart"], setup["subject_room"], mark=0.2)
    # Strong chapter: two students score high → strong
    make_tick(setup, setup["students"][0], setup["strong_subpart"], setup["subject_room"], mark=0.9)
    make_tick(setup, setup["students"][1], setup["strong_subpart"], setup["subject_room"], mark=1.0)

    ws = monday_this_week()
    stats = compute_weekly_class_stats(setup["subject_room"], ws, ws + timedelta(days=6))

    assert stats["ticks_recorded"] == 4
    assert stats["active_students"] == 2
    assert stats["class_avg_score"] == pytest.approx((0.1 + 0.2 + 0.9 + 1.0) / 4)

    struggling_names = [c["chapter_name"] for c in stats["struggling_chapters"]]
    strong_names = [c["chapter_name"] for c in stats["strong_chapters"]]
    assert "Long Division" in struggling_names
    assert "Fractions" in strong_names


@pytest.mark.django_db
def test_compute_weekly_stats_ignores_low_tick_chapters(setup):
    """A chapter with a single tick is excluded from highlight lists."""
    from openshiksha.apps.ai.analytics import compute_weekly_class_stats

    make_tick(setup, setup["students"][0], setup["weak_subpart"], setup["subject_room"], mark=0.1)

    ws = monday_this_week()
    stats = compute_weekly_class_stats(setup["subject_room"], ws, ws + timedelta(days=6))

    assert stats["ticks_recorded"] == 1
    assert stats["struggling_chapters"] == []
    assert stats["strong_chapters"] == []


# ─────────────────────────────────────────────────────────────
# llm_client tests
# ─────────────────────────────────────────────────────────────

_STATS = {
    "total_students": 24,
    "active_students": 18,
    "ticks_recorded": 200,
    "class_avg_score": 0.72,
    "struggling_chapters": [{"chapter_id": 1, "chapter_name": "Long Division", "avg_score": 0.31, "tick_count": 40}],
    "strong_chapters": [{"chapter_id": 2, "chapter_name": "Fractions", "avg_score": 0.88, "tick_count": 50}],
}


def test_build_class_summary_prompt_contains_chapters():
    from openshiksha.apps.ai.llm_client import _build_class_summary_prompt

    prompt = _build_class_summary_prompt(_STATS, "Mathematics", 8)
    assert "Long Division" in prompt
    assert "Fractions" in prompt
    assert "Standard 8 Mathematics" in prompt


def test_build_class_summary_prompt_handles_no_chapters():
    from openshiksha.apps.ai.llm_client import _build_class_summary_prompt

    empty = {**_STATS, "struggling_chapters": [], "strong_chapters": []}
    prompt = _build_class_summary_prompt(empty, "Science", 6)
    assert "none" in prompt


def test_stub_class_summary_mentions_chapters():
    from openshiksha.apps.ai.llm_client import _stub_class_summary

    text = _stub_class_summary(_STATS)
    assert "Long Division" in text
    assert "Fractions" in text
    assert "18 of 24" in text


def test_generate_class_summary_stub(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")

    with patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_class_summary(_STATS, "Mathematics", 8)

    assert result["model"] == "stub"
    assert result["input_tokens"] == 0
    assert "Long Division" in result["text"]


def test_generate_class_summary_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    mock_result = {"text": "Claude summary.", "model": "claude-sonnet-4-6", "input_tokens": 100, "output_tokens": 60}

    with patch("openshiksha.apps.ai.llm_client._call_anthropic_text", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_class_summary(_STATS, "Mathematics", 8)

    mock_call.assert_called_once()
    assert result["model"] == "claude-sonnet-4-6"


def test_generate_class_summary_google(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "fake-google")
    mock_result = {"text": "Gemma summary.", "model": "gemini-2.5-flash", "input_tokens": 90, "output_tokens": 50}

    with patch("openshiksha.apps.ai.llm_client._call_google_ai_studio", return_value=mock_result) as mock_call:
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_class_summary(_STATS, "Mathematics", 8)

    mock_call.assert_called_once()
    assert result["model"] == "gemini-2.5-flash"


def test_generate_class_summary_ollama(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "")
    mock_result = {"text": "Ollama summary.", "model": "ollama/gemma3:4b", "input_tokens": 30, "output_tokens": 20}

    with (
        patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=True),
        patch("openshiksha.apps.ai.llm_client._call_ollama", return_value=mock_result) as mock_call,
    ):
        from openshiksha.apps.ai import llm_client

        result = llm_client.generate_class_summary(_STATS, "Mathematics", 8)

    mock_call.assert_called_once()
    assert "ollama" in result["model"]


# ─────────────────────────────────────────────────────────────
# Task tests
# ─────────────────────────────────────────────────────────────

MOCK_SUMMARY = {
    "text": "18 of 24 students practised this week.",
    "model": "claude-sonnet-4-6",
    "input_tokens": 110,
    "output_tokens": 55,
}


def test_monday_of_week():
    from datetime import date

    from openshiksha.apps.ai.tasks import _monday_of_week

    # 2026-05-27 is a Wednesday → Monday is 2026-05-25
    assert _monday_of_week(date(2026, 5, 27)) == date(2026, 5, 25)
    # A Monday maps to itself
    assert _monday_of_week(date(2026, 5, 25)) == date(2026, 5, 25)


@pytest.mark.django_db
def test_generate_weekly_report_task_default_week(setup):
    from openshiksha.apps.ai.models import WeeklyClassReport
    from openshiksha.apps.ai.tasks import generate_weekly_class_report

    make_tick(setup, setup["students"][0], setup["strong_subpart"], setup["subject_room"], mark=0.9)
    make_tick(setup, setup["students"][1], setup["strong_subpart"], setup["subject_room"], mark=1.0)

    with patch("openshiksha.apps.ai.llm_client.generate_class_summary", return_value=MOCK_SUMMARY):
        result = generate_weekly_class_report(setup["subject_room"].pk)

    report = WeeklyClassReport.objects.get(pk=result["report_id"])
    assert report.week_start == monday_this_week()
    assert report.week_end == monday_this_week() + timedelta(days=6)
    assert report.active_students == 2
    assert report.summary_text == MOCK_SUMMARY["text"]
    assert report.model_used == "claude-sonnet-4-6"
    assert report.input_tokens == 110


@pytest.mark.django_db
def test_generate_weekly_report_task_explicit_week_snaps_to_monday(setup):
    from openshiksha.apps.ai.models import WeeklyClassReport
    from openshiksha.apps.ai.tasks import generate_weekly_class_report

    # Pass a Wednesday; task should snap week_start back to the preceding Monday.
    wednesday = "2026-05-27"
    with patch("openshiksha.apps.ai.llm_client.generate_class_summary", return_value=MOCK_SUMMARY):
        result = generate_weekly_class_report(setup["subject_room"].pk, week_start_iso=wednesday)

    report = WeeklyClassReport.objects.get(pk=result["report_id"])
    assert report.week_start.isoformat() == "2026-05-25"


@pytest.mark.django_db
def test_generate_weekly_report_task_idempotent(setup):
    from openshiksha.apps.ai.models import WeeklyClassReport
    from openshiksha.apps.ai.tasks import generate_weekly_class_report

    with patch("openshiksha.apps.ai.llm_client.generate_class_summary", return_value=MOCK_SUMMARY):
        r1 = generate_weekly_class_report(setup["subject_room"].pk)
        r2 = generate_weekly_class_report(setup["subject_room"].pk)

    assert r1["report_id"] == r2["report_id"]
    assert WeeklyClassReport.objects.filter(subject_room=setup["subject_room"]).count() == 1


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
def report(db, setup):
    from openshiksha.apps.ai.models import WeeklyClassReport

    ws = monday_this_week()
    return WeeklyClassReport.objects.create(
        subject_room=setup["subject_room"],
        week_start=ws,
        week_end=ws + timedelta(days=6),
        summary_text="Weekly summary narrative.",
        total_students=3,
        active_students=2,
        ticks_recorded=12,
        class_avg_score=0.65,
        model_used="stub",
    )


@pytest.mark.django_db
def test_api_list_reports_teacher(api_client, setup, report):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/weekly-reports/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["summary_text"] == "Weekly summary narrative."
    assert resp.data["results"][0]["participation_rate"] == pytest.approx(2 / 3)


@pytest.mark.django_db
def test_api_list_reports_filter_by_room(api_client, setup, report):
    auth(api_client, setup["teacher"])
    resp = api_client.get(f"/api/v1/ai/weekly-reports/?subject_room={setup['subject_room'].pk}")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_api_other_teacher_sees_no_reports(api_client, setup, report):
    auth(api_client, setup["other_teacher"])
    resp = api_client.get("/api/v1/ai/weekly-reports/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_student_sees_no_reports(api_client, setup, report):
    auth(api_client, setup["students"][0])
    resp = api_client.get("/api/v1/ai/weekly-reports/")
    assert resp.status_code == 200
    assert len(resp.data["results"]) == 0


@pytest.mark.django_db
def test_api_retrieve_report(api_client, setup, report):
    auth(api_client, setup["teacher"])
    resp = api_client.get(f"/api/v1/ai/weekly-reports/{report.pk}/")
    assert resp.status_code == 200
    assert resp.data["class_avg_score"] == pytest.approx(0.65)


@pytest.mark.django_db
def test_api_latest_report(api_client, setup, report):
    auth(api_client, setup["teacher"])
    resp = api_client.get(f"/api/v1/ai/weekly-reports/latest/?subject_room={setup['subject_room'].pk}")
    assert resp.status_code == 200
    assert resp.data["id"] == report.pk


@pytest.mark.django_db
def test_api_latest_requires_subject_room(api_client, setup, report):
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/weekly-reports/latest/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_latest_404_when_none(api_client, setup):
    auth(api_client, setup["teacher"])
    resp = api_client.get(f"/api/v1/ai/weekly-reports/latest/?subject_room={setup['subject_room'].pk}")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_api_latest_student_forbidden(api_client, setup, report):
    auth(api_client, setup["students"][0])
    resp = api_client.get(f"/api/v1/ai/weekly-reports/latest/?subject_room={setup['subject_room'].pk}")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_generate_report_queues_task(api_client, setup):
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.generate_weekly_class_report") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/weekly-reports/generate/",
            {"subject_room_id": setup["subject_room"].pk},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(setup["subject_room"].pk, None)


@pytest.mark.django_db
def test_api_generate_report_with_week_start(api_client, setup):
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.generate_weekly_class_report") as mock_task:
        mock_task.delay = MagicMock()
        resp = api_client.post(
            "/api/v1/ai/weekly-reports/generate/",
            {"subject_room_id": setup["subject_room"].pk, "week_start": "2026-05-25"},
            format="json",
        )
    assert resp.status_code == 202
    mock_task.delay.assert_called_once_with(setup["subject_room"].pk, "2026-05-25")


@pytest.mark.django_db
def test_api_generate_report_not_owner_forbidden(api_client, setup):
    auth(api_client, setup["other_teacher"])
    resp = api_client.post(
        "/api/v1/ai/weekly-reports/generate/",
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_generate_report_student_forbidden(api_client, setup):
    auth(api_client, setup["students"][0])
    resp = api_client.post(
        "/api/v1/ai/weekly-reports/generate/",
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_unauthenticated_forbidden(api_client):
    resp = api_client.get("/api/v1/ai/weekly-reports/")
    assert resp.status_code == 401
