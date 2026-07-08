"""
Management command: import_content_pack

The first **writer** into the community content pipeline (CP-2). It takes a
content-pack JSON file authored by an outside contributor, validates it with the
pure CP-1 validator, and stages the *whole pack as one* ``ContentSubmission`` row
in the ``PENDING`` state — it never touches the live question bank. Materializing
the pack's questions into the shared bank is a separate, human-gated step
(approval in CP-3/CP-4), so unreviewed external content can never reach a
student through this command.

Idempotency (decided 2026-07-07): the pack's canonical-JSON ``content_pack_hash``
is the identity key. If a submission with that hash is already ``PENDING`` or
``APPROVED``, the import is a no-op ("already staged / already approved") — it
does **not** create a duplicate and does **not** auto-supersede anything (the
schema carries no stable pack id, so import cannot tell "a newer version of pack
X" from "a brand-new pack"; ``superseded`` is a review-time action only). A pack
that was previously ``REJECTED`` or ``SUPERSEDED`` *can* be re-staged as a fresh
``PENDING`` row.

Usage::

    python manage.py import_content_pack path/to/pack.json
    python manage.py import_content_pack path/to/pack.json --dry-run

``--dry-run`` validates and reports what *would* happen without writing anything.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from openshiksha.apps.core.content_packs import (
    ContentPackError,
    content_pack_hash,
    validate_content_pack,
)
from openshiksha.apps.core.models import ContentSubmission, ContentSubmissionState

#: States in which an existing row already "holds" this pack, so a re-import is a
#: no-op. A REJECTED/SUPERSEDED pack is not live, so it may be re-staged.
_BLOCKING_STATES = (ContentSubmissionState.PENDING, ContentSubmissionState.APPROVED)


class Command(BaseCommand):
    help = "Validate a content pack (CP-1) and stage it as a PENDING ContentSubmission (CP-2)."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help="Path to a content-pack JSON file (validated against the CP-1 schema).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report what would happen, but write nothing to the DB.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        dry_run = options.get("dry_run", False)

        pack = self._load(path)
        self._validate(pack)

        pack_hash = content_pack_hash(pack)
        name = pack.get("name", "") or ""
        label = name or f"pack {pack_hash[:12]}"

        existing = (
            ContentSubmission.objects.filter(pack_hash=pack_hash, state__in=_BLOCKING_STATES)
            .order_by("-created_at")
            .first()
        )
        if existing is not None:
            self.stdout.write(
                self.style.WARNING(
                    f"'{label}' already {existing.get_state_display().lower()} "
                    f"(submission #{existing.pk}); nothing imported."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[dry-run] '{label}' is valid and would be staged as a new PENDING submission "
                    f"({len(pack.get('questions', []))} question(s), hash {pack_hash[:12]})."
                )
            )
            return

        submission = ContentSubmission.objects.create(
            name=name,
            pack_hash=pack_hash,
            provenance=pack.get("provenance", {}),
            payload=pack,
            state=ContentSubmissionState.PENDING,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Staged '{label}' as PENDING submission #{submission.pk} "
                f"({len(pack.get('questions', []))} question(s), hash {pack_hash[:12]}). "
                f"Awaiting maintainer approval — the live question bank was not touched."
            )
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _load(self, path: Path) -> dict:
        """Read + JSON-parse the pack file, raising CommandError on any I/O/parse failure."""

        if not path.is_file():
            raise CommandError(f"No such content-pack file: {path}")
        try:
            with path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} is not valid JSON: {exc}") from exc
        except OSError as exc:
            raise CommandError(f"Could not read {path}: {exc}") from exc

    def _validate(self, pack) -> None:
        """Run the CP-1 validator, surfacing every error as a clean CommandError."""

        try:
            validate_content_pack(pack)
        except ContentPackError as exc:
            lines = "\n".join(f"  - {msg}" for msg in exc.errors)
            raise CommandError(f"Content pack failed validation:\n{lines}") from exc
