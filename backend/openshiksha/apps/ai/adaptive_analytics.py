"""
Adaptive Learning Engine — analytics algorithms.

Provides pure computation functions (no DB writes) for:
- Mastery scoring (EWMA)
- SM-2 spaced repetition scheduling
- Learning path generation (topological sort + SRS interleaving)

All functions return plain dicts that Celery tasks persist to the database.
"""

from __future__ import annotations

from collections import deque
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openshiksha.apps.core.models import SubjectRoom, User

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# EWMA smoothing factor for mastery score updates (0 < alpha <= 1)
MASTERY_ALPHA = 0.3

# SM-2 thresholds
SRS_SUCCESS_THRESHOLD = 0.60
SRS_INITIAL_EF = 2.5
SRS_MIN_EF = 1.3

# Mastery score at or above which a chapter is considered "mastered"
MASTERY_SKIP_THRESHOLD = 0.80

# Days ahead to surface SRS reviews in the learning path
SRS_LOOKAHEAD_DAYS = 3


# ─────────────────────────────────────────────────────────────────────────────
# Mastery Scoring
# ─────────────────────────────────────────────────────────────────────────────


def compute_updated_mastery(current_score: float, new_score: float, attempt_count: int) -> float:
    """
    Update a student's mastery score using EWMA.

    On the very first attempt (attempt_count == 0) the raw score is used
    directly so a single attempt sets a meaningful baseline rather than
    being diluted toward 0.

    Returns the new mastery_score (0.0-1.0).
    """
    if attempt_count == 0:
        return float(new_score)
    return MASTERY_ALPHA * new_score + (1 - MASTERY_ALPHA) * current_score


def compute_mastery_for_student(student: "User", subject_room: "SubjectRoom") -> list[dict]:
    """
    Compute updated StudentMastery data for all KnowledgeNodes in a SubjectRoom.

    Aggregates scores per chapter from all graded submissions, applies EWMA
    on top of existing mastery rows, and returns update descriptors.

    Returns a list of dicts::

        {
            "knowledge_node_id": int,
            "new_mastery_score": float,
            "mastery_level": str,
            "attempt_count": int,
            "last_attempted_at": datetime,
        }
    """
    from django.db.models import Avg, Count, Max

    from openshiksha.apps.ai.models import KnowledgeNode, MasteryLevel, StudentMastery
    from openshiksha.apps.core.models import Submission

    submissions_qs = (
        Submission.objects.filter(
            student=student,
            assignment__subject_room=subject_room,
            score__isnull=False,
            submitted_at__isnull=False,
        )
        .values("assignment__problem_set__chapter_id")
        .annotate(
            avg_score=Avg("score"),
            attempt_count=Count("id"),
            last_at=Max("submitted_at"),
        )
    )

    chapter_data: dict[int, dict] = {
        row["assignment__problem_set__chapter_id"]: row
        for row in submissions_qs
        if row["assignment__problem_set__chapter_id"] is not None
    }

    if not chapter_data:
        return []

    existing_mastery: dict[int, StudentMastery] = {
        m.knowledge_node_id: m
        for m in StudentMastery.objects.filter(
            student=student,
            knowledge_node__subject=subject_room.subject,
            knowledge_node__chapter_id__in=list(chapter_data.keys()),
        ).select_related("knowledge_node")
    }

    chapter_to_node: dict[int, int] = {
        node.chapter_id: node.pk
        for node in KnowledgeNode.objects.filter(
            subject=subject_room.subject,
            chapter_id__in=list(chapter_data.keys()),
            is_active=True,
        )
    }

    results = []
    for chapter_id, agg in chapter_data.items():
        node_id = chapter_to_node.get(chapter_id)
        if node_id is None:
            continue

        existing = existing_mastery.get(node_id)
        current_score = existing.mastery_score if existing else 0.0
        current_attempts = existing.attempt_count if existing else 0

        new_score = compute_updated_mastery(current_score, float(agg["avg_score"]), current_attempts)
        new_level = StudentMastery.level_from_score(new_score) if new_score > 0 else MasteryLevel.UNKNOWN

        results.append(
            {
                "knowledge_node_id": node_id,
                "new_mastery_score": round(new_score, 6),
                "mastery_level": new_level,
                "attempt_count": current_attempts + int(agg["attempt_count"]),
                "last_attempted_at": agg["last_at"],
            }
        )

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Spaced Repetition (SM-2)
# ─────────────────────────────────────────────────────────────────────────────


def compute_srs_update(
    score: float,
    current_interval: int,
    current_ef: float,
    current_repetitions: int,
) -> dict:
    """
    Apply SM-2 algorithm to compute updated SRS scheduling values.

    Returns::

        {
            "interval_days": int,
            "easiness_factor": float,
            "repetitions": int,
        }
    """
    if score >= SRS_SUCCESS_THRESHOLD:
        if current_repetitions == 0:
            new_interval = 1
        elif current_repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(current_interval * current_ef))

        new_ef = max(SRS_MIN_EF, current_ef + 0.1 - (1.0 - score) * 0.8)
        new_repetitions = current_repetitions + 1
    else:
        new_interval = 1
        new_ef = current_ef
        new_repetitions = 0

    return {
        "interval_days": new_interval,
        "easiness_factor": round(new_ef, 4),
        "repetitions": new_repetitions,
    }


def get_due_srs_entries(student: "User", subject_room: "SubjectRoom") -> list[dict]:
    """
    Return KnowledgeNode IDs that are due (or upcoming) for spaced review.

    Includes entries due within the next SRS_LOOKAHEAD_DAYS days so the
    learning path can proactively schedule upcoming reviews.

    Returns list of dicts::

        {"knowledge_node_id": int, "next_review_date": date, "interval_days": int}
    """
    from django.utils import timezone

    from openshiksha.apps.ai.models import SpacedRepetitionEntry

    lookahead = timezone.localdate() + timedelta(days=SRS_LOOKAHEAD_DAYS)

    entries = SpacedRepetitionEntry.objects.filter(
        student=student,
        knowledge_node__subject=subject_room.subject,
        next_review_date__lte=lookahead,
    ).values("knowledge_node_id", "next_review_date", "interval_days")

    return list(entries)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────────────
# Learning Path Generation
# ─────────────────────────────────────────────────────────────────────────────


def _topological_sort_nodes(nodes: list, prerequisite_map: dict[int, list[int]]) -> list:
    """
    Topologically sort KnowledgeNode instances by prerequisite edges.

    Uses Kahn's algorithm (BFS). Nodes with no prerequisites come first;
    ties broken by chapter.order. Cycle residue is appended by chapter.order.

    Returns a list of KnowledgeNode instances in learning order.
    """
    node_map = {n.pk: n for n in nodes}
    node_ids = set(node_map.keys())

    in_degree: dict[int, int] = {nid: 0 for nid in node_ids}
    adj: dict[int, list[int]] = {nid: [] for nid in node_ids}

    for nid in node_ids:
        for prereq_id in prerequisite_map.get(nid, []):
            if prereq_id in node_ids:
                adj[prereq_id].append(nid)
                in_degree[nid] += 1

    queue = deque(
        sorted(
            [nid for nid, deg in in_degree.items() if deg == 0],
            key=lambda nid: getattr(node_map[nid].chapter, "order", 0),
        )
    )

    result = []
    while queue:
        nid = queue.popleft()
        result.append(node_map[nid])
        for successor in sorted(
            adj[nid],
            key=lambda sid: getattr(node_map[sid].chapter, "order", 0),
        ):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    visited = {n.pk for n in result}
    remaining = sorted(
        [node_map[nid] for nid in node_ids if nid not in visited],
        key=lambda n: getattr(n.chapter, "order", 0),
    )
    result.extend(remaining)

    return result


def _best_problem_set_for_chapter(student: "User", subject_room: "SubjectRoom", chapter_id: int):
    """
    Return the ID of the most relevant problem set for a student in a chapter.

    Priority:
    1. Assigned problem set not yet submitted by this student
    2. Any active problem set for the chapter
    Returns None if nothing is available.
    """
    from openshiksha.apps.core.models import Assignment, ProblemSet

    assigned_ps_ids = list(
        Assignment.objects.filter(subject_room=subject_room, problem_set__chapter_id=chapter_id)
        .exclude(submissions__student=student)
        .values_list("problem_set_id", flat=True)
        .order_by("problem_set__number")
    )
    if assigned_ps_ids:
        return assigned_ps_ids[0]

    return (
        ProblemSet.objects.filter(chapter_id=chapter_id, is_active=True)
        .order_by("number")
        .values_list("id", flat=True)
        .first()
    )


def generate_learning_path_steps(student: "User", subject_room: "SubjectRoom") -> list[dict]:
    """
    Generate an ordered list of learning path step descriptors for a student.

    Algorithm:
    1. Load all active KnowledgeNodes for this subject
    2. Load the student's current mastery levels
    3. Filter out mastered nodes (score >= MASTERY_SKIP_THRESHOLD)
    4. Topologically sort remaining nodes respecting prerequisites
    5. Interleave SRS-due review nodes at the front (mastered but due for review)
    6. Pick a suggested problem_set for each step

    Returns a list of step descriptor dicts::

        {
            "knowledge_node_id": int,
            "position": int,
            "is_review": bool,
            "problem_set_id": int | None,
        }
    """
    from openshiksha.apps.ai.models import KnowledgeNode, StudentMastery

    nodes = list(
        KnowledgeNode.objects.filter(subject=subject_room.subject, is_active=True)
        .select_related("chapter")
        .prefetch_related("prerequisites")
    )

    if not nodes:
        return []

    node_ids = [n.pk for n in nodes]

    mastery_map: dict[int, float] = {
        m.knowledge_node_id: m.mastery_score
        for m in StudentMastery.objects.filter(
            student=student,
            knowledge_node_id__in=node_ids,
        )
    }

    unmastered = [n for n in nodes if mastery_map.get(n.pk, 0.0) < MASTERY_SKIP_THRESHOLD]

    prerequisite_map: dict[int, list[int]] = {n.pk: [p.pk for p in n.prerequisites.all()] for n in nodes}

    sorted_nodes = _topological_sort_nodes(unmastered, prerequisite_map)

    due_srs = get_due_srs_entries(student, subject_room)
    due_node_ids = {entry["knowledge_node_id"] for entry in due_srs}

    all_node_map = {n.pk: n for n in nodes}
    sorted_node_ids = {n.pk for n in sorted_nodes}

    # Mastered nodes that are due for review (not already in the learning queue)
    extra_review_nodes = [
        all_node_map[nid] for nid in due_node_ids if nid not in sorted_node_ids and nid in all_node_map
    ]

    steps = []
    position = 1

    for node in extra_review_nodes:
        ps_id = _best_problem_set_for_chapter(student, subject_room, node.chapter_id)
        steps.append(
            {
                "knowledge_node_id": node.pk,
                "position": position,
                "is_review": True,
                "problem_set_id": ps_id,
            }
        )
        position += 1

    for node in sorted_nodes:
        ps_id = _best_problem_set_for_chapter(student, subject_room, node.chapter_id)
        steps.append(
            {
                "knowledge_node_id": node.pk,
                "position": position,
                "is_review": node.pk in due_node_ids,
                "problem_set_id": ps_id,
            }
        )
        position += 1

    return steps
