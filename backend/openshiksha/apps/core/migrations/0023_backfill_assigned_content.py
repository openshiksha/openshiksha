"""
AIV-1 backfill: populate ``Assignment.assigned_content`` for every existing
assignment by snapshotting its live problem set right now.

Pre-existing assignments necessarily have no record of what they "originally
contained" (no version history existed before this migration). The live set is
the best-available truth and gives us the integrity guarantee from this point
forward: any *future* edit to the live set leaves the snapshot untouched.

Idempotent: rows that already have a snapshot are skipped, so re-running is
safe.
"""

from __future__ import annotations

from datetime import datetime, timezone

from django.db import migrations

SNAPSHOT_SCHEMA_VERSION = 1


def _build_snapshot_via_historical(problem_set, QuestionSubpart):
    question_rows = list(problem_set.questions.order_by("id").values("id", "question_type", "difficulty", "stem_text"))
    question_ids = [row["id"] for row in question_rows]
    subparts_by_question: dict[int, list[dict]] = {qid: [] for qid in question_ids}
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
                    "interactive_html": sp.interactive_html or "",
                    "is_interactive": bool(sp.is_interactive),
                }
            )

    questions = []
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


def backfill_assigned_content(apps, schema_editor):
    Assignment = apps.get_model("core", "Assignment")
    QuestionSubpart = apps.get_model("core", "QuestionSubpart")
    backfilled = 0
    for assignment in Assignment.objects.filter(assigned_content__isnull=True).select_related("problem_set"):
        assignment.assigned_content = _build_snapshot_via_historical(assignment.problem_set, QuestionSubpart)
        assignment.save(update_fields=["assigned_content"])
        backfilled += 1
    print(f"  backfilled {backfilled} assignment(s)")


def noop_reverse(apps, schema_editor):
    # Reversing the snapshot capture is a no-op — the field is nullable so a
    # plain field removal in the parent migration handles the schema side.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0022_assignment_assigned_content"),
    ]

    operations = [
        migrations.RunPython(backfill_assigned_content, noop_reverse),
    ]
