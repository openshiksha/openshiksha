"""
Core analytics algorithms for the AI feature.

All functions are pure computation: they accept Django querysets / model instances
and return plain dicts that the Celery tasks persist to the database.

Algorithms are intentionally heuristic (no external ML/LLM dependencies) so they
work offline with zero extra infra. The interface is designed for future upgrading
— swap the internals, keep the return shapes.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db.models import Count, Sum
from django.utils import timezone

if TYPE_CHECKING:
    from datetime import datetime

    from openshiksha.apps.core.models import SubjectRoom, User

# Minimum ticks required before we consider the data meaningful
MIN_TICKS_FOR_GAP = 3
MIN_TICKS_FOR_PREDICTION = 5

# How many days after a gap is resolved before we suggest spaced review
SPACED_REVIEW_DAYS = 7

# Max recommendations to include in a single daily practice plan
MAX_PLAN_RECOMMENDATIONS = 5

# Default minutes per recommendation when problem set has no estimate
DEFAULT_MINUTES_PER_REC = 10

# Score threshold below which a student is "struggling"
STRUGGLE_THRESHOLD = 0.50

# A gap is resolved when score rises above this
RESOLVED_THRESHOLD = 0.60

# Recency window for performance prediction (days)
RECENCY_WINDOW_DAYS = 30


# ─────────────────────────────────────────────────────────────────────────────
# Learning Gap Detection
# ─────────────────────────────────────────────────────────────────────────────


def detect_gaps_for_student(student: "User", subject_room: "SubjectRoom") -> list[dict]:
    """
    Analyse all Ticks for a student in a SubjectRoom and return a list of
    detected/resolved gap dicts keyed by chapter.

    Return format:
    [
        {
            "chapter_id": int,
            "avg_score": float,
            "tick_count": int,
            "severity": str | None,   # None means gap is resolved / not a gap
            "is_resolved": bool,
        },
        ...
    ]

    Only chapters with at least MIN_TICKS_FOR_GAP ticks are included.
    """
    from openshiksha.apps.edge.models import Tick

    # Aggregate ticks by chapter via question_subpart → question → chapter
    rows = (
        Tick.objects.filter(student=student, subject_room=subject_room)
        .values("question_subpart__question__chapter_id")
        .annotate(
            total_marks=Sum("mark"),
            tick_count=Count("id"),
        )
    )

    results = []
    for row in rows:
        chapter_id = row["question_subpart__question__chapter_id"]
        if chapter_id is None:
            continue
        tick_count = row["tick_count"]
        if tick_count < MIN_TICKS_FOR_GAP:
            continue

        avg_score = row["total_marks"] / tick_count

        if avg_score >= RESOLVED_THRESHOLD:
            # Previously flagged gaps with this chapter may be resolved
            results.append(
                {
                    "chapter_id": chapter_id,
                    "avg_score": avg_score,
                    "tick_count": tick_count,
                    "severity": None,
                    "is_resolved": True,
                }
            )
        elif avg_score < STRUGGLE_THRESHOLD:
            from openshiksha.apps.ai.models import LearningGap

            results.append(
                {
                    "chapter_id": chapter_id,
                    "avg_score": avg_score,
                    "tick_count": tick_count,
                    "severity": LearningGap.severity_for_score(avg_score),
                    "is_resolved": False,
                }
            )

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Class Insight Generation
# ─────────────────────────────────────────────────────────────────────────────


def generate_insights_for_subject_room(subject_room: "SubjectRoom") -> list[dict]:
    """
    Analyse all students' Ticks in a SubjectRoom grouped by chapter and return
    class-level insight dicts.

    Return format:
    [
        {
            "chapter_id": int,
            "class_avg_score": float,
            "students_assessed": int,
            "students_struggling": int,
            "pct_struggling": float,
            "insight_type": str,
        },
        ...
    ]

    Only chapters where at least 2 students have been assessed are included.
    """
    from openshiksha.apps.ai.models import ClassInsight
    from openshiksha.apps.edge.models import Tick

    # Per-student per-chapter totals in this subject_room
    per_student_rows = (
        Tick.objects.filter(subject_room=subject_room)
        .values("student_id", "question_subpart__question__chapter_id")
        .annotate(
            total_marks=Sum("mark"),
            tick_count=Count("id"),
        )
    )

    # Reorganise into: chapter_id → list of (avg_score_per_student)
    chapter_scores: dict[int, list[float]] = defaultdict(list)
    for row in per_student_rows:
        chapter_id = row["question_subpart__question__chapter_id"]
        if chapter_id is None or row["tick_count"] == 0:
            continue
        avg = row["total_marks"] / row["tick_count"]
        chapter_scores[chapter_id].append(avg)

    results = []
    for chapter_id, scores in chapter_scores.items():
        if len(scores) < 2:
            continue

        students_assessed = len(scores)
        class_avg = sum(scores) / students_assessed
        struggling = sum(1 for s in scores if s < STRUGGLE_THRESHOLD)
        pct_struggling = struggling / students_assessed

        results.append(
            {
                "chapter_id": chapter_id,
                "class_avg_score": class_avg,
                "students_assessed": students_assessed,
                "students_struggling": struggling,
                "pct_struggling": pct_struggling,
                "insight_type": ClassInsight.insight_type_for_pct(pct_struggling),
            }
        )

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Performance Prediction
# ─────────────────────────────────────────────────────────────────────────────


def _sigmoid(x: float) -> float:
    """Normalised sigmoid: maps x in [0, ∞) → (0, 1)."""
    return 1.0 / (1.0 + math.exp(-x))


def predict_performance_for_student(student: "User", subject_room: "SubjectRoom") -> dict | None:
    """
    Compute a heuristic performance prediction for a student in a subject_room.

    Algorithm:
    1. Fetch all Ticks for this student + subject_room.
    2. Split into recent (last RECENCY_WINDOW_DAYS days) and older.
    3. Weighted average: recent ticks count 2×, older ticks count 1×.
    4. Confidence = sigmoid(tick_count / 20) — grows with evidence.
    5. Determine trend: compare recent vs older average.
    6. Identify top 3 strong/weak chapters.

    Returns None if fewer than MIN_TICKS_FOR_PREDICTION ticks exist.

    Return format:
    {
        "predicted_score": float,
        "confidence": float,
        "readiness_level": str,
        "tick_count": int,
        "factors": {
            "strong_chapters": [{"chapter_id": int, "avg_score": float}, ...],
            "weak_chapters":   [{"chapter_id": int, "avg_score": float}, ...],
            "recent_trend": "improving" | "declining" | "stable",
        }
    }
    """
    from openshiksha.apps.ai.models import PerformancePrediction
    from openshiksha.apps.edge.models import Tick

    cutoff = timezone.now() - timedelta(days=RECENCY_WINDOW_DAYS)

    ticks = list(
        Tick.objects.filter(student=student, subject_room=subject_room).values(
            "mark", "created_at", "question_subpart__question__chapter_id"
        )
    )

    if len(ticks) < MIN_TICKS_FOR_PREDICTION:
        return None

    recent = [t for t in ticks if t["created_at"] >= cutoff]
    older = [t for t in ticks if t["created_at"] < cutoff]

    recent_avg = sum(t["mark"] for t in recent) / len(recent) if recent else None
    older_avg = sum(t["mark"] for t in older) / len(older) if older else None

    # Weighted average
    weight_sum = 2 * len(recent) + len(older)
    weighted_total = 2 * sum(t["mark"] for t in recent) + sum(t["mark"] for t in older)
    predicted_score = weighted_total / weight_sum

    # Confidence
    confidence = _sigmoid((len(ticks) / 20) - 2)  # low until ~20 ticks

    # Trend
    if recent_avg is not None and older_avg is not None:
        diff = recent_avg - older_avg
        if diff > 0.05:
            trend = "improving"
        elif diff < -0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Per-chapter averages for factor identification
    chapter_totals: dict[int, list[float]] = defaultdict(list)
    for t in ticks:
        cid = t["question_subpart__question__chapter_id"]
        if cid is not None:
            chapter_totals[cid].append(t["mark"])

    chapter_avgs = [
        {"chapter_id": cid, "avg_score": sum(scores) / len(scores)}
        for cid, scores in chapter_totals.items()
        if len(scores) >= MIN_TICKS_FOR_GAP
    ]
    chapter_avgs.sort(key=lambda x: x["avg_score"])

    weak_chapters = [c for c in chapter_avgs if c["avg_score"] < STRUGGLE_THRESHOLD][:3]
    strong_chapters = [c for c in reversed(chapter_avgs) if c["avg_score"] >= RESOLVED_THRESHOLD][:3]

    return {
        "predicted_score": round(predicted_score, 4),
        "confidence": round(confidence, 4),
        "readiness_level": PerformancePrediction.readiness_for_score(predicted_score),
        "tick_count": len(ticks),
        "factors": {
            "strong_chapters": strong_chapters,
            "weak_chapters": weak_chapters,
            "recent_trend": trend,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Content Recommendations
# ─────────────────────────────────────────────────────────────────────────────


def generate_recommendations_for_student(
    student: "User",
    subject_room: "SubjectRoom",
) -> list[dict]:
    """
    Generate content recommendation dicts for a student in a SubjectRoom.

    Algorithm (priority order):
    1. Active severe gaps → URGENT
    2. Recently resolved gaps (resolved ≤ SPACED_REVIEW_DAYS ago) → HIGH (spaced review)
    3. Active moderate gaps → HIGH
    4. Active mild gaps → MEDIUM
    5. Next unvisited chapters (by order) where student has no ticks yet → LOW

    Each dict specifies what chapter to recommend, why, and which problem set
    to attempt (the next unsubmitted problem set in the chapter, if any).

    Return format:
    [
        {
            "chapter_id": int,
            "reason": str,       # RecommendationReason value
            "priority": int,     # RecommendationPriority value
            "score_snapshot": float | None,
            "problem_set_id": int | None,
        },
        ...
    ]
    """
    from openshiksha.apps.ai.models import ContentRecommendation, LearningGap, RecommendationReason

    now = timezone.now()
    spaced_cutoff = now - timedelta(days=SPACED_REVIEW_DAYS)

    results: list[dict] = []
    seen_chapters: set[int] = set()

    # ── 1. Active gaps (severe + moderate + mild) ──────────────────────────
    active_gaps = (
        LearningGap.objects.filter(student=student, subject_room=subject_room, is_resolved=False)
        .select_related("chapter")
        .order_by("avg_score")  # lowest score first = most urgent
    )

    for gap in active_gaps:
        if gap.chapter_id in seen_chapters:
            continue
        seen_chapters.add(gap.chapter_id)

        reason = _reason_for_severity(gap.severity)
        results.append(
            {
                "chapter_id": gap.chapter_id,
                "reason": reason,
                "priority": ContentRecommendation.priority_for_reason(reason),
                "score_snapshot": round(gap.avg_score, 4),
                "problem_set_id": _best_problem_set_for_chapter(student, subject_room, gap.chapter_id),
            }
        )

    # ── 2. Recently resolved gaps → spaced review ─────────────────────────
    resolved_gaps = (
        LearningGap.objects.filter(
            student=student,
            subject_room=subject_room,
            is_resolved=True,
            refreshed_at__gte=spaced_cutoff,
        )
        .select_related("chapter")
        .order_by("refreshed_at")
    )

    for gap in resolved_gaps:
        if gap.chapter_id in seen_chapters:
            continue
        seen_chapters.add(gap.chapter_id)
        results.append(
            {
                "chapter_id": gap.chapter_id,
                "reason": RecommendationReason.SPACED_REVIEW,
                "priority": ContentRecommendation.priority_for_reason(RecommendationReason.SPACED_REVIEW),
                "score_snapshot": round(gap.avg_score, 4),
                "problem_set_id": _best_problem_set_for_chapter(student, subject_room, gap.chapter_id),
            }
        )

    # ── 3. Next unvisited chapters (progression) ──────────────────────────
    from openshiksha.apps.edge.models import Tick

    visited_chapter_ids = set(
        Tick.objects.filter(student=student, subject_room=subject_room)
        .values_list("question_subpart__question__chapter_id", flat=True)
        .distinct()
    )

    # Chapters that belong to this subject + standard, ordered by curriculum order
    subject = subject_room.subject
    standard = subject_room.classroom.standard
    next_chapters = (
        subject.chapters.filter(standard=standard)
        .exclude(id__in=visited_chapter_ids)
        .order_by("order")[:3]  # suggest up to 3 next topics
    )

    for chapter in next_chapters:
        if chapter.id in seen_chapters:
            continue
        seen_chapters.add(chapter.id)
        results.append(
            {
                "chapter_id": chapter.id,
                "reason": RecommendationReason.NEXT_TOPIC,
                "priority": ContentRecommendation.priority_for_reason(RecommendationReason.NEXT_TOPIC),
                "score_snapshot": None,
                "problem_set_id": _best_problem_set_for_chapter(student, subject_room, chapter.id),
            }
        )

    # Sort by priority ascending (1=urgent first), then by score_snapshot ascending
    results.sort(key=lambda r: (r["priority"], r["score_snapshot"] or 1.0))
    return results


def build_practice_plan(
    student: "User",
    subject_room: "SubjectRoom",
    recommendations: list[dict],
) -> dict:
    """
    Given a sorted list of recommendation dicts (from generate_recommendations_for_student),
    build a daily practice plan dict.

    Selects the top MAX_PLAN_RECOMMENDATIONS items by priority and computes
    estimated minutes based on linked problem sets.

    Return format:
    {
        "chapter_ids": [int, ...],       # ordered list of recommended chapter IDs
        "estimated_minutes": int,
    }
    """
    from openshiksha.apps.core.models import ProblemSet

    top = recommendations[:MAX_PLAN_RECOMMENDATIONS]

    total_minutes = 0
    for rec in top:
        ps_id = rec.get("problem_set_id")
        if ps_id:
            try:
                ps = ProblemSet.objects.only("estimated_minutes").get(pk=ps_id)
                total_minutes += ps.estimated_minutes or DEFAULT_MINUTES_PER_REC
            except ProblemSet.DoesNotExist:
                total_minutes += DEFAULT_MINUTES_PER_REC
        else:
            total_minutes += DEFAULT_MINUTES_PER_REC

    return {
        "chapter_ids": [r["chapter_id"] for r in top],
        "estimated_minutes": total_minutes,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Weekly Class Report (Teacher AI Assistant)
# ─────────────────────────────────────────────────────────────────────────────

# Max chapters surfaced in the weekly report's strong/struggling lists
WEEKLY_REPORT_TOP_N = 3

# Minimum ticks in a chapter before it is eligible for the weekly highlight lists
MIN_TICKS_FOR_WEEKLY_CHAPTER = 2


def compute_weekly_class_stats(
    subject_room: "SubjectRoom",
    week_start,
    week_end,
) -> dict:
    """
    Compute a deterministic statistics snapshot for a SubjectRoom over a week.

    The window is [week_start 00:00, week_end 23:59:59] in the active timezone,
    matched against Tick.created_at.

    Return format:
    {
        "total_students": int,
        "active_students": int,
        "ticks_recorded": int,
        "class_avg_score": float,          # 0.0–1.0, 0.0 when no ticks
        "struggling_chapters": [           # up to WEEKLY_REPORT_TOP_N, weakest first
            {"chapter_id", "chapter_name", "avg_score", "tick_count"}, ...
        ],
        "strong_chapters": [               # up to WEEKLY_REPORT_TOP_N, strongest first
            {"chapter_id", "chapter_name", "avg_score", "tick_count"}, ...
        ],
    }
    """
    from datetime import datetime, time

    from openshiksha.apps.edge.models import Tick

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(week_start, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(week_end, time.max), tz)

    total_students = subject_room.students.count()

    week_ticks = Tick.objects.filter(
        subject_room=subject_room,
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    )

    ticks_recorded = week_ticks.count()
    active_students = week_ticks.values("student_id").distinct().count()

    if ticks_recorded == 0:
        return {
            "total_students": total_students,
            "active_students": 0,
            "ticks_recorded": 0,
            "class_avg_score": 0.0,
            "struggling_chapters": [],
            "strong_chapters": [],
        }

    overall = week_ticks.aggregate(total=Sum("mark"), n=Count("id"))
    class_avg_score = (overall["total"] or 0.0) / overall["n"]

    chapter_rows = (
        week_ticks.values(
            "question_subpart__question__chapter_id",
            "question_subpart__question__chapter__name",
        )
        .annotate(total_marks=Sum("mark"), tick_count=Count("id"))
        .filter(tick_count__gte=MIN_TICKS_FOR_WEEKLY_CHAPTER)
    )

    chapters = []
    for row in chapter_rows:
        chapter_id = row["question_subpart__question__chapter_id"]
        if chapter_id is None:
            continue
        chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_name": row["question_subpart__question__chapter__name"],
                "avg_score": round(row["total_marks"] / row["tick_count"], 4),
                "tick_count": row["tick_count"],
            }
        )

    chapters_by_score = sorted(chapters, key=lambda c: c["avg_score"])
    struggling = [c for c in chapters_by_score if c["avg_score"] < STRUGGLE_THRESHOLD][:WEEKLY_REPORT_TOP_N]
    strong = [c for c in reversed(chapters_by_score) if c["avg_score"] >= RESOLVED_THRESHOLD][:WEEKLY_REPORT_TOP_N]

    return {
        "total_students": total_students,
        "active_students": active_students,
        "ticks_recorded": ticks_recorded,
        "class_avg_score": round(class_avg_score, 4),
        "struggling_chapters": struggling,
        "strong_chapters": strong,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Assignment Draft Builder
# ─────────────────────────────────────────────────────────────────────────────

# How far back to look at Tick data when ranking class weakness for a draft
ASSIGNMENT_DRAFT_LOOKBACK_DAYS = 45
# Default / cap on the number of questions a draft contains
ASSIGNMENT_DRAFT_DEFAULT_SIZE = 8
ASSIGNMENT_DRAFT_MAX_SIZE = 20
# How many weak chapters a single draft spreads across
ASSIGNMENT_DRAFT_TOP_CHAPTERS = 4
# Minimum ticks in a chapter before its class average is trustworthy
MIN_TICKS_FOR_DRAFT_CHAPTER = 3
# Skip questions that were assigned to this room within the last N days
RECENT_ASSIGNMENT_WINDOW_DAYS = 60
# Fallback per-question time estimate when nothing better is available
DEFAULT_MINUTES_PER_QUESTION = 3


def rank_weak_chapters_for_room(
    subject_room: "SubjectRoom",
    lookback_days: int = ASSIGNMENT_DRAFT_LOOKBACK_DAYS,
    limit: int = ASSIGNMENT_DRAFT_TOP_CHAPTERS,
) -> list[dict]:
    """
    Rank the chapters a SubjectRoom is weakest on over a recent window.

    Aggregates every Tick in the room within ``lookback_days`` by chapter and
    returns the lowest-scoring chapters first. Struggling chapters (avg below
    STRUGGLE_THRESHOLD) are preferred; if the class isn't struggling anywhere we
    still return the weakest chapters so the teacher always gets a usable draft.

    Each entry: {"chapter_id", "chapter_name", "avg_score", "tick_count"}.
    """
    from openshiksha.apps.edge.models import Tick

    since = timezone.now() - timedelta(days=lookback_days)
    rows = (
        Tick.objects.filter(subject_room=subject_room, created_at__gte=since)
        .values(
            "question_subpart__question__chapter_id",
            "question_subpart__question__chapter__name",
        )
        .annotate(total_marks=Sum("mark"), tick_count=Count("id"))
        .filter(tick_count__gte=MIN_TICKS_FOR_DRAFT_CHAPTER)
    )

    chapters = []
    for row in rows:
        chapter_id = row["question_subpart__question__chapter_id"]
        if chapter_id is None:
            continue
        chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_name": row["question_subpart__question__chapter__name"],
                "avg_score": round(row["total_marks"] / row["tick_count"], 4),
                "tick_count": row["tick_count"],
            }
        )

    chapters.sort(key=lambda c: (c["avg_score"], -c["tick_count"]))
    struggling = [c for c in chapters if c["avg_score"] < STRUGGLE_THRESHOLD]
    ranked = struggling or chapters
    return ranked[:limit]


def _recent_question_ids_for_room(subject_room: "SubjectRoom") -> set[int]:
    """Question IDs already assigned to this room within the recency window."""
    from openshiksha.apps.core.models import Assignment

    since = timezone.now() - timedelta(days=RECENT_ASSIGNMENT_WINDOW_DAYS)
    return set(
        Assignment.objects.filter(subject_room=subject_room, assigned_at__gte=since).values_list(
            "problem_set__questions__id", flat=True
        )
    )


def _allocate_per_chapter(num_chapters: int, size: int) -> list[int]:
    """
    Split ``size`` question slots across ``num_chapters`` weakest-first.

    The weakest chapter gets the extra slots when size isn't divisible, so a
    draft leans toward where the class struggles most.
    """
    if num_chapters <= 0:
        return []
    base = size // num_chapters
    remainder = size % num_chapters
    return [base + (1 if i < remainder else 0) for i in range(num_chapters)]


def _question_preview(question) -> str:
    """Short plain-text preview of a question's first subpart prompt."""
    first = question.subparts.order_by("index").first()
    text = (first.question_text if first else "") or ""
    text = " ".join(text.split())
    return text[:140]


def build_assignment_draft(
    subject_room: "SubjectRoom",
    size: int = ASSIGNMENT_DRAFT_DEFAULT_SIZE,
    target_difficulty: int = 2,
) -> dict:
    """
    Deterministically assemble a draft assignment targeting class weaknesses.

    Ranks the room's weakest chapters, then fills ``size`` slots with active
    questions from those chapters (within the room's standard + subject), nearest
    the requested difficulty first and skipping items assigned to the room
    recently. No LLM is used here — the result is reproducible and offline-safe.

    Returns:
        {
            "target_chapters": [...],
            "selected_questions": [...],   # ordered, with per-item reason
            "estimated_minutes": int,
            "title": str,
            "error": str | None,           # set when nothing could be built
        }
    """
    size = max(1, min(size, ASSIGNMENT_DRAFT_MAX_SIZE))
    target_difficulty = max(1, min(target_difficulty, 5))

    weak_chapters = rank_weak_chapters_for_room(subject_room)
    if not weak_chapters:
        return {
            "target_chapters": [],
            "selected_questions": [],
            "estimated_minutes": 0,
            "title": "",
            "error": "Not enough recent practice data to identify weak chapters for this class.",
        }

    standard = subject_room.classroom.standard
    subject = subject_room.subject
    used_ids = _recent_question_ids_for_room(subject_room)

    allocation = _allocate_per_chapter(len(weak_chapters), size)
    selected: list[dict] = []
    chosen_ids: set[int] = set()

    # First pass: honour the per-chapter allocation.
    for chapter, want in zip(weak_chapters, allocation):
        if want <= 0:
            continue
        picks = _pick_questions_for_chapter(
            standard,
            subject,
            chapter["chapter_id"],
            target_difficulty,
            want,
            exclude=used_ids | chosen_ids,
        )
        for q in picks:
            chosen_ids.add(q["question_id"])
            q["reason"] = (
                f"Targets {chapter['chapter_name']}, where the class is averaging " f"{chapter['avg_score']:.0%}."
            )
            selected.append(q)

    # Second pass: backfill any shortfall (a chapter ran out of fresh questions)
    # from the remaining weak chapters, weakest first.
    if len(selected) < size:
        for chapter in weak_chapters:
            if len(selected) >= size:
                break
            picks = _pick_questions_for_chapter(
                standard,
                subject,
                chapter["chapter_id"],
                target_difficulty,
                size - len(selected),
                exclude=used_ids | chosen_ids,
            )
            for q in picks:
                chosen_ids.add(q["question_id"])
                q["reason"] = (
                    f"Extra practice on {chapter['chapter_name']} " f"(class average {chapter['avg_score']:.0%})."
                )
                selected.append(q)

    if not selected:
        return {
            "target_chapters": weak_chapters,
            "selected_questions": [],
            "estimated_minutes": 0,
            "title": "",
            "error": (
                "The weakest chapters have no unused questions in the bank. "
                "Add questions or generate some with AI first."
            ),
        }

    estimated_minutes = sum(q["estimated_minutes"] for q in selected)
    for q in selected:
        q.pop("estimated_minutes", None)

    weakest_name = weak_chapters[0]["chapter_name"]
    title = f"Practice: {weakest_name}"
    if len({q["chapter_id"] for q in selected}) > 1:
        title = f"Targeted practice — {subject.name}"

    return {
        "target_chapters": weak_chapters,
        "selected_questions": selected,
        "estimated_minutes": estimated_minutes,
        "title": title,
        "error": None,
    }


def _pick_questions_for_chapter(
    standard,
    subject,
    chapter_id: int,
    target_difficulty: int,
    want: int,
    exclude: set[int],
) -> list[dict]:
    """Pick up to ``want`` active questions for a chapter, nearest difficulty first."""
    from openshiksha.apps.core.models import Question

    candidates = list(
        Question.objects.filter(
            standard=standard,
            subject=subject,
            chapter_id=chapter_id,
            is_active=True,
        )
        .exclude(id__in=exclude)
        .prefetch_related("subparts")
    )
    # Closest to the requested difficulty first; id as a deterministic tiebreaker.
    candidates.sort(key=lambda q: (abs(q.difficulty - target_difficulty), q.pk))

    out = []
    for q in candidates[:want]:
        out.append(
            {
                "question_id": q.pk,
                "chapter_id": chapter_id,
                "chapter_name": q.chapter.name,
                "difficulty": q.difficulty,
                "question_type": q.question_type,
                "preview": _question_preview(q),
                "estimated_minutes": DEFAULT_MINUTES_PER_QUESTION,
            }
        )
    return out


# ── Helpers ──────────────────────────────────────────────────────────────────


def _reason_for_severity(severity: str) -> str:
    from openshiksha.apps.ai.models import GapSeverity, RecommendationReason

    mapping = {
        GapSeverity.SEVERE: RecommendationReason.SEVERE_GAP,
        GapSeverity.MODERATE: RecommendationReason.MODERATE_GAP,
        GapSeverity.MILD: RecommendationReason.MILD_GAP,
    }
    return mapping.get(severity, RecommendationReason.MILD_GAP)  # type: ignore[call-overload]


def _best_problem_set_for_chapter(
    student: "User",
    subject_room: "SubjectRoom",
    chapter_id: int,
) -> int | None:
    """
    Return the ID of the best problem set to recommend for this chapter.

    Strategy:
    1. Look for problem sets in the chapter that are already assigned in this
       subject_room and the student hasn't submitted yet — return the lowest-numbered one.
    2. Fall back to the lowest-numbered active problem set in the chapter.
    3. Return None if no problem sets exist.
    """
    from openshiksha.apps.core.models import Assignment, ProblemSet

    # Assigned and not yet submitted
    assigned_ps_ids = (
        Assignment.objects.filter(subject_room=subject_room, problem_set__chapter_id=chapter_id)
        .exclude(submissions__student=student)
        .values_list("problem_set_id", flat=True)
        .order_by("problem_set__number")
    )
    if assigned_ps_ids:
        return assigned_ps_ids[0]

    # Any active problem set for this chapter
    ps = (
        ProblemSet.objects.filter(chapter_id=chapter_id, is_active=True)
        .order_by("number")
        .values_list("id", flat=True)
        .first()
    )
    return ps


# ─────────────────────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard
# ─────────────────────────────────────────────────────────────────────────────

PARENT_TOP_CHAPTERS = 3
MIN_TICKS_FOR_PARENT_CHAPTER = 2
MAX_HOME_ACTIVITIES = 3
INACTIVITY_ALERT_DAYS = 7
SCORE_DROP_ALERT_THRESHOLD = 0.15
SEVERE_SCORE_THRESHOLD = 0.40


def compute_parent_weekly_stats(child, week_start, week_end) -> dict:
    """
    Compute a deterministic snapshot of a child's week for parent dashboards.

    Returns a dict shaped for ParentProgressSummary.* fields plus a few extras
    consumed by the LLM prompt and stub:

    {
        "child_name": str,
        "grade_level": int,
        "ticks_recorded": int,
        "active_days": int,
        "avg_score": float,
        "prev_avg_score": float,
        "score_delta": float,
        "weak_chapters": [{"chapter_id", "chapter_name", "avg_score", "tick_count"}, ...],
        "strong_chapters": [...],
        "subjects_active": [str, ...],
        "days_since_last_tick": int | None,   # None when the child has never practised
    }
    """
    from datetime import datetime, time, timedelta

    from openshiksha.apps.edge.models import Tick

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(week_start, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(week_end, time.max), tz)
    prev_start_dt = start_dt - timedelta(days=7)

    week_ticks = Tick.objects.filter(student=child, created_at__gte=start_dt, created_at__lte=end_dt)
    ticks_recorded = week_ticks.count()
    active_days = week_ticks.dates("created_at", "day").count()

    if ticks_recorded == 0:
        avg_score = 0.0
    else:
        agg = week_ticks.aggregate(total=Sum("mark"), n=Count("id"))
        avg_score = (agg["total"] or 0.0) / agg["n"]

    prev_ticks = Tick.objects.filter(student=child, created_at__gte=prev_start_dt, created_at__lt=start_dt)
    prev_count = prev_ticks.count()
    if prev_count == 0:
        prev_avg_score = 0.0
        score_delta = 0.0
    else:
        prev_agg = prev_ticks.aggregate(total=Sum("mark"), n=Count("id"))
        prev_avg_score = (prev_agg["total"] or 0.0) / prev_agg["n"]
        score_delta = avg_score - prev_avg_score if ticks_recorded else 0.0

    weak_chapters: list[dict] = []
    strong_chapters: list[dict] = []
    subjects_active: list[str] = []

    if ticks_recorded > 0:
        chapter_rows = (
            week_ticks.values(
                "question_subpart__question__chapter_id",
                "question_subpart__question__chapter__name",
            )
            .annotate(total_marks=Sum("mark"), tick_count=Count("id"))
            .filter(tick_count__gte=MIN_TICKS_FOR_PARENT_CHAPTER)
        )

        chapters: list[dict] = []
        for row in chapter_rows:
            chapter_id = row["question_subpart__question__chapter_id"]
            if chapter_id is None:
                continue
            chapters.append(
                {
                    "chapter_id": chapter_id,
                    "chapter_name": row["question_subpart__question__chapter__name"],
                    "avg_score": round(row["total_marks"] / row["tick_count"], 4),
                    "tick_count": row["tick_count"],
                }
            )

        by_score = sorted(chapters, key=lambda c: c["avg_score"])
        weak_chapters = [c for c in by_score if c["avg_score"] < STRUGGLE_THRESHOLD][:PARENT_TOP_CHAPTERS]
        strong_chapters = [c for c in reversed(by_score) if c["avg_score"] >= RESOLVED_THRESHOLD][:PARENT_TOP_CHAPTERS]

        subjects_active = sorted(
            {
                name
                for name in week_ticks.values_list("question_subpart__question__subject__name", flat=True).distinct()
                if name
            }
        )

    last_tick = Tick.objects.filter(student=child).order_by("-created_at").values_list("created_at", flat=True).first()
    if last_tick is None:
        days_since_last_tick = None
    else:
        days_since_last_tick = max(0, (timezone.now() - last_tick).days)

    return {
        "child_name": child.full_name if hasattr(child, "full_name") else child.username,
        "grade_level": int(getattr(child, "grade", None) or 8),
        "ticks_recorded": ticks_recorded,
        "active_days": active_days,
        "avg_score": round(avg_score, 4),
        "prev_avg_score": round(prev_avg_score, 4),
        "score_delta": round(score_delta, 4),
        "weak_chapters": weak_chapters,
        "strong_chapters": strong_chapters,
        "subjects_active": subjects_active,
        "days_since_last_tick": days_since_last_tick,
    }


def build_home_activities(stats: dict) -> list[dict]:
    """
    Suggest concrete at-home activities for the parent, derived from the weak
    chapters in the weekly stats. Heuristic — no LLM call needed.
    """
    activities: list[dict] = []
    for chapter in stats.get("weak_chapters", [])[:MAX_HOME_ACTIVITIES]:
        name = chapter.get("chapter_name", "this chapter")
        activities.append(
            {
                "title": f"Practise {name} together",
                "description": (
                    f"Spend 15 minutes working through 3–5 questions on {name} with your child. "
                    f"Ask them to explain each step out loud — teaching it back helps the concept stick."
                ),
                "chapter_name": name,
            }
        )

    if not activities and stats.get("strong_chapters"):
        top = stats["strong_chapters"][0].get("chapter_name", "their strongest chapter")
        activities.append(
            {
                "title": f"Celebrate progress in {top}",
                "description": (
                    f"Your child is doing well in {top}. Ask them to teach you one idea from it — "
                    f"this builds their confidence and reinforces what they have learned."
                ),
                "chapter_name": top,
            }
        )
    return activities


def build_parent_alerts(stats: dict) -> list[dict]:
    """Compute parent alerts purely from the stats snapshot — no LLM call."""
    from openshiksha.apps.ai.models import ParentAlertSeverity

    alerts: list[dict] = []

    days_since = stats.get("days_since_last_tick")
    if days_since is None:
        alerts.append(
            {
                "severity": ParentAlertSeverity.ATTENTION,
                "label": "No practice yet",
                "detail": "Your child has not attempted any questions yet. Encourage them to start with one short set.",
            }
        )
    elif days_since >= INACTIVITY_ALERT_DAYS:
        alerts.append(
            {
                "severity": ParentAlertSeverity.ATTENTION,
                "label": f"Inactive for {days_since} days",
                "detail": "Your child has not practised in over a week. A short daily routine helps build momentum.",
            }
        )

    if stats.get("score_delta", 0.0) <= -SCORE_DROP_ALERT_THRESHOLD and stats.get("ticks_recorded", 0) > 0:
        alerts.append(
            {
                "severity": ParentAlertSeverity.URGENT,
                "label": "Sharp drop in scores",
                "detail": (
                    f"Average dropped by {abs(stats['score_delta']):.0%} vs last week. "
                    f"It may help to revisit the weakest chapter together."
                ),
            }
        )

    severe = [c for c in stats.get("weak_chapters", []) if c.get("avg_score", 1.0) < SEVERE_SCORE_THRESHOLD]
    if severe:
        names = ", ".join(c["chapter_name"] for c in severe[:2])
        alerts.append(
            {
                "severity": ParentAlertSeverity.URGENT,
                "label": "Struggling badly in key chapters",
                "detail": f"Below 40% in: {names}. Consider asking the teacher for additional support.",
            }
        )

    if stats.get("score_delta", 0.0) >= SCORE_DROP_ALERT_THRESHOLD and stats.get("ticks_recorded", 0) > 0:
        alerts.append(
            {
                "severity": ParentAlertSeverity.INFO,
                "label": "Strong improvement this week",
                "detail": (
                    f"Average rose by {stats['score_delta']:.0%} vs last week — recognise the effort with your child."
                ),
            }
        )

    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# Class Misconception Insights
# ─────────────────────────────────────────────────────────────────────────────

# Default lookback window for clustering — recent enough to be actionable,
# wide enough to capture a misconception that surfaced across multiple sessions.
CLUSTER_LOOKBACK_DAYS = 30

# A misconception only "counts" as a class-level cluster once at least this many
# distinct students share it. One student stumbling is just one student.
CLUSTER_MIN_STUDENTS = 2


def _normalise_misconception_label(label: str) -> str:
    """Normalise a free-text misconception label so near-duplicates merge.

    Lowercases, collapses whitespace, strips trailing punctuation. We deliberately
    keep this conservative — semantic clustering is a future upgrade; the labels
    the LLM produces today already overlap enough that case/whitespace folding
    collapses most duplicates.
    """
    if not label:
        return ""
    cleaned = " ".join(label.strip().lower().split())
    return cleaned.rstrip(".!?,;:")


def cluster_misconceptions_for_subject_room(
    subject_room: "SubjectRoom",
    lookback_days: int = CLUSTER_LOOKBACK_DAYS,
) -> tuple[list[dict], "datetime"]:
    """Aggregate recent StudentMisconception rows for a SubjectRoom into clusters.

    Looks at misconceptions detected in the last ``lookback_days`` for students
    enrolled in the room and groups them by normalised label. Clusters with
    fewer than ``CLUSTER_MIN_STUDENTS`` distinct students are dropped — a single
    student's wrong answer isn't a class-level signal.

    Returns ``(clusters, window_start)``. Each cluster dict shape::

        {
            "misconception_label": str,    # normalised, lowercase
            "student_count": int,          # distinct students
            "occurrence_count": int,       # total rows
            "sample_diagnosis": str,       # representative diagnosis line
            "sample_remediation_tip": str, # representative remediation tip
            "last_seen": datetime,         # most recent detected_at in this cluster
        }

    Sorted by ``student_count`` desc, then ``last_seen`` desc.
    """
    from openshiksha.apps.ai.models import StudentMisconception

    window_start = timezone.now() - timedelta(days=lookback_days)
    student_ids = list(subject_room.students.values_list("pk", flat=True))
    if not student_ids:
        return [], window_start

    qs = (
        StudentMisconception.objects.filter(
            student_id__in=student_ids,
            detected_at__gte=window_start,
        )
        .only(
            "student_id",
            "misconception_label",
            "diagnosis_text",
            "remediation_tip",
            "detected_at",
        )
        .order_by("-detected_at")
    )

    buckets: dict[str, dict] = {}
    for m in qs:
        key = _normalise_misconception_label(m.misconception_label)
        if not key:
            continue
        bucket = buckets.setdefault(
            key,
            {
                "misconception_label": key,
                "student_ids": set(),
                "occurrence_count": 0,
                "sample_diagnosis": "",
                "sample_remediation_tip": "",
                "last_seen": m.detected_at,
            },
        )
        bucket["student_ids"].add(m.student_id)
        bucket["occurrence_count"] += 1
        # Because qs is ordered detected_at DESC, the first record we see is the
        # newest — keep its prose as the representative sample.
        if not bucket["sample_diagnosis"] and m.diagnosis_text:
            bucket["sample_diagnosis"] = m.diagnosis_text
        if not bucket["sample_remediation_tip"] and m.remediation_tip:
            bucket["sample_remediation_tip"] = m.remediation_tip
        if m.detected_at > bucket["last_seen"]:
            bucket["last_seen"] = m.detected_at

    clusters = []
    for bucket in buckets.values():
        count = len(bucket["student_ids"])
        if count < CLUSTER_MIN_STUDENTS:
            continue
        clusters.append(
            {
                "misconception_label": bucket["misconception_label"],
                "student_count": count,
                "occurrence_count": bucket["occurrence_count"],
                "sample_diagnosis": bucket["sample_diagnosis"],
                "sample_remediation_tip": bucket["sample_remediation_tip"],
                "last_seen": bucket["last_seen"],
            }
        )

    clusters.sort(key=lambda c: (-c["student_count"], -c["last_seen"].timestamp()))
    return clusters, window_start
