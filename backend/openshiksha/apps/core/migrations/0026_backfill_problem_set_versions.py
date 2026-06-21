"""
AIV-7: backfill ``ProblemSetVersion`` rows + populate ``Assignment.problem_set_version``
from each existing assignment's ``assigned_content``.

For each ``(problem_set_id, content_hash)`` pair we hold exactly one version —
identical content across multiple assignments collapses into a single row. The
``content`` JSON is taken from the assignment's own snapshot so a future
read against the FK returns byte-for-byte what the snapshot had.

Idempotent: skips assignments that already have a ``problem_set_version`` set,
and uses ``get_or_create`` semantics for the version row.
"""

from __future__ import annotations

import hashlib
import json

from django.db import migrations
from django.db.models import Max


def _content_hash(snapshot: dict) -> str:
    canonical = json.dumps(snapshot.get("questions") or [], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def backfill(apps, schema_editor):
    Assignment = apps.get_model("core", "Assignment")
    ProblemSetVersion = apps.get_model("core", "ProblemSetVersion")

    minted = 0
    linked = 0
    skipped = 0

    # Iterate deterministically so two identical snapshots map to the same first
    # winner if they happen to be inserted concurrently with a future run.
    qs = (
        Assignment.objects.filter(
            problem_set_version__isnull=True,
            assigned_content__isnull=False,
        )
        .select_related("problem_set")
        .order_by("pk")
    )

    for assignment in qs.iterator():
        snapshot = assignment.assigned_content
        if not snapshot:
            skipped += 1
            continue

        h = _content_hash(snapshot)
        version = ProblemSetVersion.objects.filter(problem_set_id=assignment.problem_set_id, content_hash=h).first()
        if version is None:
            next_number = (
                ProblemSetVersion.objects.filter(problem_set_id=assignment.problem_set_id).aggregate(
                    m=Max("version_number")
                )["m"]
                or 0
            ) + 1
            version = ProblemSetVersion.objects.create(
                problem_set_id=assignment.problem_set_id,
                version_number=next_number,
                content_hash=h,
                content=snapshot,
                created_by=None,
            )
            minted += 1

        assignment.problem_set_version = version
        assignment.save(update_fields=["problem_set_version"])
        linked += 1

    print(f"  AIV-7 backfill: minted {minted} version(s), linked {linked} assignment(s), skipped {skipped}.")


def noop_reverse(apps, schema_editor):
    # Reversing the data migration is a no-op — the schema-level field removal
    # in the prior migration handles the storage side, and we don't try to
    # reconstruct ``assigned_content`` on the way back (it's still populated).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0025_problem_set_version"),
    ]

    operations = [
        migrations.RunPython(backfill, noop_reverse),
    ]
