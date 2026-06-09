"""
Assignment content snapshots (AIV-1).

When an assignment is created, we capture a frozen copy of the problem set's
questions in ``Assignment.assigned_content``. The grader and the student
serializer read from this snapshot, so editing the live ProblemSet, Question,
or QuestionSubpart after the fact can never silently re-grade already-assigned
work or change what a student sees mid-assignment.

The snapshot shape is intentionally a strict superset of what the grader and the
student renderer need — see ``build_assignment_snapshot`` below. ``subpart_id``
is preserved exactly because croupier seeds on (student_id, subpart_id) and
losing that breaks per-student randomization determinism.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openshiksha.apps.core.models import ProblemSet


SNAPSHOT_SCHEMA_VERSION = 1


def build_assignment_snapshot(problem_set: "ProblemSet") -> dict[str, Any]:
    """
    Build a frozen JSON-serializable snapshot of ``problem_set``'s questions.

    The shape is stable across schema versions; older snapshots remain readable
    because reader sites tolerate missing optional fields. Bump
    ``SNAPSHOT_SCHEMA_VERSION`` and write a migration when a *required* field
    changes meaning.
    """
    from openshiksha.apps.core.models import QuestionSubpart

    # Stable order: by ProblemSetQuestion through-table primary key isn't
    # exposed cheaply, so use Question.id ordering. The grader and renderer
    # are order-tolerant per question, but a stable order keeps the snapshot
    # byte-deterministic for the byte-identical regression test.
    question_rows = list(
        problem_set.questions.order_by("id").values(
            "id",
            "question_type",
            "difficulty",
            "stem_text",
        )
    )
    question_ids = [row["id"] for row in question_rows]

    subparts_by_question: dict[int, list[dict[str, Any]]] = {qid: [] for qid in question_ids}
    if question_ids:
        for sp in QuestionSubpart.objects.filter(question_id__in=question_ids).order_by("question_id", "index", "id"):
            subparts_by_question.setdefault(sp.question_id, []).append(
                {
                    "subpart_id": sp.id,
                    "index": sp.index,
                    "subpart_type": sp.subpart_type or "",
                    "question_text": sp.question_text or "",
                    "options": sp.options,
                    "correct_answer": sp.correct_answer,
                    "variable_constraints": sp.variable_constraints,
                    "image_url": sp.image_url or "",
                    "solution_text": sp.solution_text or "",
                    "hint_text": sp.hint_text or "",
                    "widget_kind": sp.widget_kind or "",
                    "widget_config": sp.widget_config,
                    # Legacy escape hatch — see QuestionSubpart.interactive_html.
                    "interactive_html": sp.interactive_html or "",
                    "is_interactive": bool(sp.is_interactive),
                }
            )

    questions: list[dict[str, Any]] = []
    for row in question_rows:
        questions.append(
            {
                "question_id": row["id"],
                "question_type": row["question_type"],
                "difficulty": row["difficulty"],
                "stem_text": row["stem_text"] or "",
                "subparts": subparts_by_question.get(row["id"], []),
            }
        )

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "problem_set_id": problem_set.pk,
        "problem_set_title": problem_set.title,
        "questions": questions,
    }


def iter_snapshot_subparts(snapshot: dict[str, Any] | None):
    """
    Yield ``(question_dict, subpart_dict)`` pairs from a snapshot, in the same
    (question_id, index) order the grader expects. Tolerates ``None`` (returns
    empty) so callers can fall back to the live set when no snapshot exists.
    """
    if not snapshot:
        return
    for question in snapshot.get("questions") or []:
        for subpart in question.get("subparts") or []:
            yield question, subpart
