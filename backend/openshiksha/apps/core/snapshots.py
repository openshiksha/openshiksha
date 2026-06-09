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


def snapshot_has_drifted(snapshot: dict[str, Any] | None, problem_set: "ProblemSet") -> bool:
    """
    AIV-5: report whether the live ``problem_set`` has drifted from a frozen
    ``snapshot`` (i.e. anything the renderer or grader cares about has
    changed since assign time). A no-snapshot assignment is treated as not
    drifted — there's nothing to drift from.

    Compares the snapshot's ``questions`` block to a freshly-built one,
    ignoring volatile keys (``captured_at``, ``problem_set_title``) that
    don't affect what students see or how grading runs.
    """
    if not snapshot or not snapshot.get("questions"):
        return False
    fresh = build_assignment_snapshot(problem_set)
    return snapshot.get("questions") != fresh.get("questions")


def _content_hash(snapshot: dict[str, Any]) -> str:
    """
    AIV-7: stable hash over the meaningful part of a snapshot — the ``questions``
    block. Excludes volatile fields like ``captured_at`` and ``problem_set_title``
    so equivalent content always hashes the same and ``ProblemSetVersion``'s
    ``unique_together(problem_set, content_hash)`` actually dedups.
    """
    import hashlib
    import json

    canonical = json.dumps(snapshot.get("questions") or [], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_or_create_version_for(problem_set, *, created_by=None):
    """
    AIV-7: idempotent factory for ``ProblemSetVersion`` rows. Builds a fresh
    snapshot of the live ``problem_set``, hashes the meaningful content, and
    returns the existing row for that hash if it exists — minting a new one
    with the next ``version_number`` otherwise.

    ``created_by`` is recorded on new rows for audit; ignored on cache hits.
    Returns a tuple ``(version, created)`` mirroring Django's get_or_create.
    """
    from django.db import transaction
    from django.db.models import Max

    from openshiksha.apps.core.models import ProblemSetVersion

    fresh = build_assignment_snapshot(problem_set)
    h = _content_hash(fresh)

    with transaction.atomic():
        existing = ProblemSetVersion.objects.select_for_update().filter(problem_set=problem_set, content_hash=h).first()
        if existing is not None:
            return existing, False
        next_number = (
            ProblemSetVersion.objects.filter(problem_set=problem_set).aggregate(m=Max("version_number"))["m"] or 0
        ) + 1
        version = ProblemSetVersion.objects.create(
            problem_set=problem_set,
            version_number=next_number,
            content_hash=h,
            content=fresh,
            created_by=created_by,
        )
        return version, True


def resolve_assignment_content(assignment) -> dict[str, Any] | None:
    """
    AIV-7: single source of truth for "what was assigned." Reads
    ``assignment.problem_set_version.content`` when the FK is populated and
    falls back to the legacy ``assigned_content`` JSONField otherwise. Every
    snapshot reader (grader, student serializer, drift check, diff helpers)
    routes through this so the cutover from JSONField to FK is atomic.
    """
    version = getattr(assignment, "problem_set_version", None)
    if version is not None:
        return version.content
    return getattr(assignment, "assigned_content", None)


def diff_snapshots(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    """
    AIV-6: structured diff for the re-sync blast-radius preview. Compares two
    snapshot dicts (typically an assignment's current frozen snapshot vs a
    fresh one built from the live set) and reports:

    - ``questions_added``    — question_ids present in ``new`` but not ``old``
    - ``questions_removed``  — question_ids present in ``old`` but not ``new``
    - ``answer_changes``     — subparts whose ``correct_answer`` changed; each
      row carries ``{subpart_id, question_id, before, after}`` so the UI can
      explain *what* changes when a student is re-graded
    - ``content_changes``    — subparts whose ``question_text``/``options``/
      ``variable_constraints``/widget config changed but whose answer didn't.
      Affects what the student would see but not how grading scores them.

    Output is JSON-safe and intended for both API responses and structured logs.
    """
    old = old or {}
    old_qs = {q["question_id"]: q for q in old.get("questions") or []}
    new_qs = {q["question_id"]: q for q in new.get("questions") or []}

    questions_added = sorted(set(new_qs) - set(old_qs))
    questions_removed = sorted(set(old_qs) - set(new_qs))

    answer_changes: list[dict[str, Any]] = []
    content_changes: list[dict[str, Any]] = []

    cosmetic_keys = (
        "question_text",
        "options",
        "variable_constraints",
        "widget_kind",
        "widget_config",
        "image_url",
    )

    for qid in set(old_qs) & set(new_qs):
        old_subparts = {sp["subpart_id"]: sp for sp in old_qs[qid].get("subparts") or []}
        new_subparts = {sp["subpart_id"]: sp for sp in new_qs[qid].get("subparts") or []}
        for sp_id in set(old_subparts) | set(new_subparts):
            old_sp = old_subparts.get(sp_id)
            new_sp = new_subparts.get(sp_id)
            if not old_sp or not new_sp:
                # Subpart added/removed under a shared question — counts as
                # answer-affecting because grading scope changes.
                answer_changes.append(
                    {
                        "subpart_id": sp_id,
                        "question_id": qid,
                        "before": old_sp.get("correct_answer") if old_sp else None,
                        "after": new_sp.get("correct_answer") if new_sp else None,
                    }
                )
                continue
            if old_sp.get("correct_answer") != new_sp.get("correct_answer"):
                answer_changes.append(
                    {
                        "subpart_id": sp_id,
                        "question_id": qid,
                        "before": old_sp.get("correct_answer"),
                        "after": new_sp.get("correct_answer"),
                    }
                )
                continue
            if any(old_sp.get(k) != new_sp.get(k) for k in cosmetic_keys):
                content_changes.append({"subpart_id": sp_id, "question_id": qid})

    return {
        "questions_added": questions_added,
        "questions_removed": questions_removed,
        "answer_changes": answer_changes,
        "content_changes": content_changes,
    }


def render_snapshot_for_student(
    snapshot: dict[str, Any],
    *,
    student_id: int | None,
    include_solutions: bool,
) -> list[dict[str, Any]]:
    """
    Render a snapshot's ``questions`` list into the student-facing shape that
    ``QuestionWithSubpartsStudentSerializer`` would have produced for the live
    set — but sourced from the frozen snapshot so live edits never bleed
    through. ``correct_answer`` is stripped (student-safe); per-student MCQ
    option shuffling and ``{{var}}`` substitution are applied through the same
    croupier helpers used on the live path.

    Returns a list ready to drop into ``ProblemSetStudentDetailSerializer``'s
    ``questions`` field. Response shape is preserved 1:1 with the live path.
    """
    from openshiksha.apps.api.croupier import (
        shuffle_options_for_student,
        substitute_variables,
        substitute_variables_for_student,
    )

    out: list[dict[str, Any]] = []
    for q in snapshot.get("questions") or []:
        first_sp = (q.get("subparts") or [None])[0]
        rendered_stem = q.get("stem_text") or ""
        if rendered_stem and "{{" in rendered_stem and student_id and first_sp:
            constraints = first_sp.get("variable_constraints")
            if constraints:
                from openshiksha.apps.api.croupier import sample_variable_values

                values = sample_variable_values(constraints, student_id, first_sp["subpart_id"])
                rendered_stem = substitute_variables(rendered_stem, values)

        subparts_out: list[dict[str, Any]] = []
        for sp in q.get("subparts") or []:
            sp_data: dict[str, Any] = {
                "id": sp["subpart_id"],
                "index": sp.get("index", 0),
                "subpart_type": sp.get("subpart_type") or "",
                "tags": [],  # snapshot doesn't carry tags; student-safe to omit
                "question_text": sp.get("question_text") or "",
                "options": sp.get("options"),
                "image_url": sp.get("image_url") or "",
                "hint_text": sp.get("hint_text") or "",
                "is_interactive": bool(sp.get("is_interactive")),
                "interactive_html": sp.get("interactive_html") or "",
                "widget_kind": sp.get("widget_kind") or "",
                "widget_config": sp.get("widget_config") or {},
            }
            if include_solutions:
                sp_data["solution_text"] = sp.get("solution_text") or ""

            constraints = sp.get("variable_constraints")
            if constraints and student_id:
                subst_text, subst_options, sampled_values = substitute_variables_for_student(
                    sp_data["question_text"],
                    sp_data.get("options"),
                    constraints,
                    student_id,
                    sp["subpart_id"],
                )
                sp_data["question_text"] = subst_text
                if subst_options is not None:
                    sp_data["options"] = subst_options
                if sp_data["interactive_html"]:
                    sp_data["interactive_html"] = substitute_variables(sp_data["interactive_html"], sampled_values)
                if "solution_text" in sp_data and sp_data["solution_text"]:
                    sp_data["solution_text"] = substitute_variables(sp_data["solution_text"], sampled_values)
                if sp_data["hint_text"]:
                    sp_data["hint_text"] = substitute_variables(sp_data["hint_text"], sampled_values)

            # MCQ option shuffle (same per-(student_id, subpart_id) shuffle as live path).
            sp_type = sp_data["subpart_type"]
            if sp_type in ("mcq", "multi_select") and student_id and sp_data.get("options"):
                sp_data["options"] = shuffle_options_for_student(sp_data["options"], student_id, sp["subpart_id"])

            subparts_out.append(sp_data)

        out.append(
            {
                "id": q["question_id"],
                "standard": None,
                "subject": None,
                "chapter": None,
                "question_type": q.get("question_type") or "",
                "question_type_display": (q.get("question_type") or "").replace("_", " ").title(),
                "difficulty": q.get("difficulty"),
                "stem_text": rendered_stem,
                "tags": [],
                "subparts": subparts_out,
                "is_active": True,
                "created_at": snapshot.get("captured_at"),
            }
        )
    return out


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
