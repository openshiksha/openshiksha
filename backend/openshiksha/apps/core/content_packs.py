"""
Pure, DB-free validation of a **content pack** — the keystone of the community
content pipeline (CP-1).

A content pack is a versioned JSON bundle an outside contributor authors to add
questions to the shared bank. It is *data*, validated by construction before it
is ever staged (CP-2) or approved (CP-3): widget **code** never travels this
path — only ``widget_config`` data, which is re-checked against the same vendored
per-kind schemas the live authoring surface uses.

Two validation layers, mirroring :mod:`openshiksha.apps.core.widgets`:

    1. **Structural** — the pack is validated against the vendored
       ``data/content_pack.schema.json`` (Draft 2020-12): required fields,
       field types, enums, bounds, ``additionalProperties: false``.
    2. **Per-widget** — every subpart carrying a non-blank ``widget_kind`` has
       its ``widget_config`` run through
       :func:`openshiksha.apps.core.widgets.validate_widget_config`, so a
       malformed widget config is rejected here, not discovered in the sandbox.

**On the DRF coupling (decided in CP-1):** ``validate_widget_config`` raises a
``rest_framework.serializers.ValidationError`` because it is primarily an
API-write guard. The content-pack pipeline is not an HTTP request, so we do
**not** leak that type: this module catches it and re-raises everything as a
single pack-native :class:`ContentPackError` carrying a flat, human-readable
``errors`` list. Callers (the ``import_content_pack`` command in CP-2, the CI
check in CP-5) depend only on this module's own exception, never on DRF.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from rest_framework import serializers

from openshiksha.apps.core.widgets import validate_widget_config

_SCHEMA_PATH: Path = Path(__file__).resolve().parent / "data" / "content_pack.schema.json"

#: The only pack schema version this validator understands.
SUPPORTED_PACK_VERSION = "1.0"


class ContentPackError(Exception):
    """A content pack failed validation.

    ``errors`` is a flat list of human-readable, location-scoped messages (one
    per distinct problem) so a CLI or CI job can print them verbatim. This is the
    *only* exception this module raises — the DRF ``ValidationError`` that the
    widget validator throws is caught and folded into ``errors`` so callers never
    couple to ``rest_framework``.
    """

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors) if errors else "invalid content pack")


@lru_cache(maxsize=1)
def load_content_pack_schema() -> dict:
    """Return the vendored content-pack JSON Schema (cached)."""

    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _pack_validator():
    """Build (and cache) a Draft 2020-12 validator for the pack schema."""

    from jsonschema import Draft202012Validator

    schema = load_content_pack_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _structural_errors(pack: Any) -> list[str]:
    """All JSON-Schema violations of ``pack``, as sorted, location-scoped strings."""

    errors = sorted(_pack_validator().iter_errors(pack), key=lambda e: list(e.path))
    return [_format_schema_error(err) for err in errors]


def _format_schema_error(err) -> str:  # noqa: ANN001 - jsonschema ValidationError
    """Render a jsonschema error as a path-scoped, contributor-readable message."""

    location = "/".join(str(p) for p in err.path)
    where = "pack" if not location else f"pack field '{location}'"
    return f"{where}: {err.message}"


def _widget_errors(pack: Any) -> list[str]:
    """Validate each widget-bearing subpart's config via the widget validator.

    Only runs once the structure is known to be a dict with a list of questions
    (the caller gates on structural validity first). Catches the widget
    validator's DRF ``ValidationError`` and flattens it into pack-native,
    location-scoped strings so no ``rest_framework`` type escapes this module.
    """

    messages: list[str] = []
    for q_idx, question in enumerate(pack.get("questions", [])):
        for subpart in question.get("subparts", []):
            kind = subpart.get("widget_kind", "")
            if not kind:
                continue
            s_idx = subpart.get("index", "?")
            where = f"questions[{q_idx}].subparts[index={s_idx}]"
            try:
                validate_widget_config(kind, subpart.get("widget_config", {}))
            except serializers.ValidationError as exc:
                for msg in _flatten_drf_detail(exc.detail):
                    messages.append(f"{where}: {msg}")
    return messages


def _flatten_drf_detail(detail: Any) -> list[str]:
    """Flatten a DRF ``ValidationError.detail`` (dict/list/str) into plain strings."""

    if isinstance(detail, dict):
        out: list[str] = []
        for value in detail.values():
            out.extend(_flatten_drf_detail(value))
        return out
    if isinstance(detail, (list, tuple)):
        out = []
        for item in detail:
            out.extend(_flatten_drf_detail(item))
        return out
    return [str(detail)]


def content_pack_errors(pack: Any) -> list[str]:
    """Return every validation error for ``pack`` (empty list ⇒ valid). Never raises.

    Structural errors short-circuit widget validation: there is no point running
    the widget validator over a pack whose shape we don't yet trust.
    """

    structural = _structural_errors(pack)
    if structural:
        return structural
    return _widget_errors(pack)


def validate_content_pack(pack: Any) -> None:
    """Raise :class:`ContentPackError` if ``pack`` is invalid; else return ``None``."""

    errors = content_pack_errors(pack)
    if errors:
        raise ContentPackError(errors)


def is_valid_content_pack(pack: Any) -> bool:
    """Boolean form of :func:`validate_content_pack` (never raises)."""

    return not content_pack_errors(pack)


def content_pack_hash(pack: Any) -> str:
    """A stable SHA-256 over the pack's canonical JSON.

    Key-independent of dict ordering and insignificant whitespace, so re-importing
    the byte-for-byte-equivalent pack yields the same hash. CP-2/CP-3 use this to
    make import idempotent and to key the ``superseded`` transition.
    """

    canonical = json.dumps(pack, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
