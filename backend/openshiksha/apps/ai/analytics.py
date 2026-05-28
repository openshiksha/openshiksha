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
