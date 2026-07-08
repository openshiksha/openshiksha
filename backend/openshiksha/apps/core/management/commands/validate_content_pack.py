"""
Management command: validate_content_pack

The CI half of the GitHub intake funnel (CP-5). Validates one or more
content-pack JSON files against the pure CP-1 validator and reports every
problem, file by file — **no DB access, no writes, no staging**. This is what
the ``content-packs`` CI workflow runs against ``contrib/packs/*.json`` on
every pull request, so an external contributor's pack self-checks before a
maintainer ever looks at it.

Contrast with ``import_content_pack`` (CP-2): that command *stages* a pack
into the review queue and therefore needs the database; this one only answers
"is this file a valid pack?" and exits non-zero if any file is not.

Usage::

    python manage.py validate_content_pack path/to/pack.json [more.json ...]
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


class Command(BaseCommand):
    help = "Validate content-pack JSON files against the CP-1 schema (read-only, no DB)."

    def add_arguments(self, parser):
        parser.add_argument(
            "paths",
            nargs="+",
            help="One or more content-pack JSON files to validate.",
        )

    def handle(self, *args, **options):
        failed: list[str] = []

        for raw in options["paths"]:
            path = Path(raw)
            errors = self._validate_file(path)
            if errors:
                failed.append(str(path))
                self.stderr.write(self.style.ERROR(f"✗ {path}"))
                for msg in errors:
                    self.stderr.write(f"    - {msg}")
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ {path}"))

        if failed:
            raise CommandError(
                f"{len(failed)} of {len(options['paths'])} content pack(s) failed validation: " + ", ".join(failed)
            )
        self.stdout.write(self.style.SUCCESS(f"All {len(options['paths'])} content pack(s) are valid."))

    def _validate_file(self, path: Path) -> list[str]:
        """Return a flat list of problems for one file (empty = valid)."""

        if not path.is_file():
            return ["no such file"]
        try:
            with path.open(encoding="utf-8") as fh:
                pack = json.load(fh)
        except json.JSONDecodeError as exc:
            return [f"not valid JSON: {exc}"]
        except OSError as exc:  # pragma: no cover - filesystem-dependent
            return [f"could not read: {exc}"]

        try:
            validate_content_pack(pack)
        except ContentPackError as exc:
            return exc.errors

        # Success detail: the hash is the pack's identity through the whole
        # pipeline (CP-2 idempotency key, CP-3 marker tag), so echo it here to
        # make "which submission did my PR become?" traceable later.
        self.stdout.write(f"    {len(pack.get('questions', []))} question(s), " f"hash {content_pack_hash(pack)[:12]}")
        return []
