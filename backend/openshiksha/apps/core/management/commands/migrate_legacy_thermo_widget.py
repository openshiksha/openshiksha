"""
IW-3b — one-shot migration that points the legacy thermodynamics-piston
question (Cabinet `1/1/11/3/44/22`) at the `thermo-piston` registry widget.

This command **does not** delete `interactive_html` — IW-7 deprecates that
field once the React widget (IW-2) ships and renders identically. For now it
only *adds* the kind-based path so the data model is ready the moment the
runtime + widget land.

Idempotent: safe to re-run. Supports `--dry-run` for inspection without writes.

Identification: the legacy thermo subpart is uniquely identified by carrying
`is_interactive=True` on Standard 11 / subject "Physics" (Thermodynamics
chapter). The Cabinet importer stamps the chapter + standard reliably; if more
than one match is found the command refuses to write rather than guess.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from openshiksha.apps.core.models import QuestionSubpart

# Initial config for the thermo-piston widget (IW-2). Bounds mirror the
# legacy jQuery-UI slider's min:-200 / max:200 and the piston's ~200 px of
# vertical travel. The per-student substitution still happens at serializer
# time (IW-3b), but none of the *legacy* variables (`k`, `j`) are direct
# widget inputs — they are answer-related values the student sees in the
# question text, and the widget surfaces them via `ctx.variables` as a hint
# instead of binding them to controls.
DEFAULT_THERMO_CONFIG: dict = {
    "heatMin": -200,
    "heatMax": 200,
    "workMax": 200,
    "workStep": 5,
    "title": "Thermodynamics — piston & First Law",
}

THERMO_WIDGET_KIND = "thermo-piston"


class Command(BaseCommand):
    help = "Stamp widget_kind='thermo-piston' on the legacy thermo subpart (IW-3b)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing.",
        )
        parser.add_argument(
            "--subpart-id",
            type=int,
            default=None,
            help=(
                "Optional explicit QuestionSubpart id, for tests / re-runs against "
                "a known row. When omitted the command auto-detects the legacy "
                "thermo subpart via is_interactive on Standard 11 / Physics."
            ),
        )

    def _find_subparts(self, subpart_id: int | None):
        if subpart_id is not None:
            return QuestionSubpart.objects.filter(id=subpart_id)
        return QuestionSubpart.objects.filter(
            is_interactive=True,
            question__standard__number=11,
            question__subject__name__iexact="Physics",
        )

    @transaction.atomic
    def handle(self, *args, dry_run: bool = False, subpart_id: int | None = None, **opts):
        qs = self._find_subparts(subpart_id)
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No legacy thermo subpart found — nothing to migrate."))
            return
        if count > 1 and subpart_id is None:
            raise CommandError(
                f"Found {count} interactive Std-11 Physics subparts — refuse to guess. "
                "Re-run with --subpart-id <id> to disambiguate."
            )

        updated = 0
        skipped = 0
        for sp in qs:
            if sp.widget_kind == THERMO_WIDGET_KIND and sp.widget_config:
                skipped += 1
                self.stdout.write(f"  • subpart {sp.id}: already points at {THERMO_WIDGET_KIND}; skipping")
                continue
            self.stdout.write(
                f"  • subpart {sp.id} (Q{sp.question_id}): " f"widget_kind {sp.widget_kind!r} → {THERMO_WIDGET_KIND!r}"
            )
            if not dry_run:
                sp.widget_kind = THERMO_WIDGET_KIND
                sp.widget_config = dict(DEFAULT_THERMO_CONFIG)
                sp.save(update_fields=["widget_kind", "widget_config"])
            updated += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[dry-run] would update {updated} subpart(s); skipped {skipped}."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} subpart(s); skipped {skipped}."))
