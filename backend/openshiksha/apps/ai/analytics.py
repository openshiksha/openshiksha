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

from django.db.models import Avg, Count, Sum
from django.utils import timezone

if TYPE_CHECKING:
    from openshiksha.apps.core.models import SubjectRoom, User

# Minimum ticks required before we consider the data meaningful
MIN_TICKS_FOR_GAP = 3
MIN_TICKS_FOR_PREDICTION = 5

# Score threshold below which a student is "struggling"
STRUGGLE_THRESHOLD = 0.50

# A gap is resolved when score rises above this
RESOLVED_THRESHOLD = 0.60

# Recency window for performance prediction (days)
RECENCY_WINDOW_DAYS = 30


# ─────────────────────────────────────────────────────────────────────────────
# Learning Gap Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_gaps_for_student(student: 'User', subject_room: 'SubjectRoom') -> list[dict]:
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
        Tick.objects
        .filter(student=student, subject_room=subject_room)
        .values('question_subpart__question__chapter_id')
        .annotate(
            total_marks=Sum('mark'),
            tick_count=Count('id'),
        )
    )

    results = []
    for row in rows:
        chapter_id = row['question_subpart__question__chapter_id']
        if chapter_id is None:
            continue
        tick_count = row['tick_count']
        if tick_count < MIN_TICKS_FOR_GAP:
            continue

        avg_score = row['total_marks'] / tick_count

        if avg_score >= RESOLVED_THRESHOLD:
            # Previously flagged gaps with this chapter may be resolved
            results.append({
                'chapter_id': chapter_id,
                'avg_score': avg_score,
                'tick_count': tick_count,
                'severity': None,
                'is_resolved': True,
            })
        elif avg_score < STRUGGLE_THRESHOLD:
            from openshiksha.apps.ai.models import LearningGap
            results.append({
                'chapter_id': chapter_id,
                'avg_score': avg_score,
                'tick_count': tick_count,
                'severity': LearningGap.severity_for_score(avg_score),
                'is_resolved': False,
            })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Class Insight Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_insights_for_subject_room(subject_room: 'SubjectRoom') -> list[dict]:
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
        Tick.objects
        .filter(subject_room=subject_room)
        .values('student_id', 'question_subpart__question__chapter_id')
        .annotate(
            total_marks=Sum('mark'),
            tick_count=Count('id'),
        )
    )

    # Reorganise into: chapter_id → list of (avg_score_per_student)
    chapter_scores: dict[int, list[float]] = defaultdict(list)
    for row in per_student_rows:
        chapter_id = row['question_subpart__question__chapter_id']
        if chapter_id is None or row['tick_count'] == 0:
            continue
        avg = row['total_marks'] / row['tick_count']
        chapter_scores[chapter_id].append(avg)

    results = []
    for chapter_id, scores in chapter_scores.items():
        if len(scores) < 2:
            continue

        students_assessed = len(scores)
        class_avg = sum(scores) / students_assessed
        struggling = sum(1 for s in scores if s < STRUGGLE_THRESHOLD)
        pct_struggling = struggling / students_assessed

        results.append({
            'chapter_id': chapter_id,
            'class_avg_score': class_avg,
            'students_assessed': students_assessed,
            'students_struggling': struggling,
            'pct_struggling': pct_struggling,
            'insight_type': ClassInsight.insight_type_for_pct(pct_struggling),
        })

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Performance Prediction
# ─────────────────────────────────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    """Normalised sigmoid: maps x in [0, ∞) → (0, 1)."""
    return 1.0 / (1.0 + math.exp(-x))


def predict_performance_for_student(student: 'User', subject_room: 'SubjectRoom') -> dict | None:
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
        Tick.objects
        .filter(student=student, subject_room=subject_room)
        .values('mark', 'created_at', 'question_subpart__question__chapter_id')
    )

    if len(ticks) < MIN_TICKS_FOR_PREDICTION:
        return None

    recent = [t for t in ticks if t['created_at'] >= cutoff]
    older = [t for t in ticks if t['created_at'] < cutoff]

    recent_avg = sum(t['mark'] for t in recent) / len(recent) if recent else None
    older_avg = sum(t['mark'] for t in older) / len(older) if older else None

    # Weighted average
    weight_sum = 2 * len(recent) + len(older)
    weighted_total = 2 * sum(t['mark'] for t in recent) + sum(t['mark'] for t in older)
    predicted_score = weighted_total / weight_sum

    # Confidence
    confidence = _sigmoid((len(ticks) / 20) - 2)  # low until ~20 ticks

    # Trend
    if recent_avg is not None and older_avg is not None:
        diff = recent_avg - older_avg
        if diff > 0.05:
            trend = 'improving'
        elif diff < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'

    # Per-chapter averages for factor identification
    chapter_totals: dict[int, list[float]] = defaultdict(list)
    for t in ticks:
        cid = t['question_subpart__question__chapter_id']
        if cid is not None:
            chapter_totals[cid].append(t['mark'])

    chapter_avgs = [
        {'chapter_id': cid, 'avg_score': sum(scores) / len(scores)}
        for cid, scores in chapter_totals.items()
        if len(scores) >= MIN_TICKS_FOR_GAP
    ]
    chapter_avgs.sort(key=lambda x: x['avg_score'])

    weak_chapters = [c for c in chapter_avgs if c['avg_score'] < STRUGGLE_THRESHOLD][:3]
    strong_chapters = [c for c in reversed(chapter_avgs) if c['avg_score'] >= RESOLVED_THRESHOLD][:3]

    return {
        'predicted_score': round(predicted_score, 4),
        'confidence': round(confidence, 4),
        'readiness_level': PerformancePrediction.readiness_for_score(predicted_score),
        'tick_count': len(ticks),
        'factors': {
            'strong_chapters': strong_chapters,
            'weak_chapters': weak_chapters,
            'recent_trend': trend,
        },
    }
