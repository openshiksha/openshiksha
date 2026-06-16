"""
Server-side source of truth for the Interactive Widgets Framework registry.

The frontend SDK (``frontend_modern/src/widgets/registry.ts``) is where each
widget is wired into the runtime. This module mirrors the *names* the backend
accepts, and — as of DTB-1 — enforces each kind's **per-kind JSON Schema** so a
malformed ``widget_config`` is rejected at write time, not discovered in the
sandbox.

Two layers of validation, both raising ``rest_framework.serializers``
``ValidationError`` so they surface as ``400`` through the API:

    1. **Floor** (always): ``widget_kind`` must be blank or a known registry key,
       and ``widget_config`` must be a dict (JSON object).
    2. **Per-kind schema** (when a schema is vendored for the kind): the config is
       validated against the kind's ``params.schema.json`` — types, enums,
       bounds, ``required``, ``additionalProperties: false``.

The canonical schemas are **vendored** into ``data/widget_schemas/<kind>.schema.json``
(packaged with the backend so validation works in any deployment, with or without
the frontend tree present). They are byte-identical copies of the frontend
``frontend_modern/src/widgets/<kind>/params.schema.json`` files; a parity test
(``test_widget_fields.py::TestWidgetSchemaParity``) fails CI if they drift.

``{{var}}`` template tokens are first-class: a teacher (or DTB-5's variable-aware
AI authoring) may bind a typed field to a croupier token, e.g.
``{"step": "{{s}}"}`` on ``number-line``. Such a pure-token string satisfies any
scalar type during validation; the croupier substitutes the real value
per-student before the config reaches the runtime.

This is the **guardrail keystone** the AI authoring increments (DTB-2+) ride on:
every AI-proposed config is run through :func:`validate_widget_config` before it
is rendered or stored, so malformed LLM output can never escape into the runtime
or the DB.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from rest_framework import serializers

KNOWN_WIDGET_KINDS: frozenset[str] = frozenset(
    {
        "thermo-piston",
        "number-line",
        "function-plotter",
        "fraction-bar",
        "studio-scene",
        "custom-html",
    }
)

# Vendored, packaged-with-the-backend copies of each kind's params.schema.json.
# Kinds without a file here (e.g. ``studio-scene``) fall back to floor-only
# validation — a known kind whose config is any JSON object.
_SCHEMA_DIR: Path = Path(__file__).resolve().parent / "data" / "widget_schemas"

# A string that is *nothing but* a single ``{{ var }}`` token. These are croupier
# bindings that get substituted per-student before render, so during authoring
# validation they stand in for a value of any scalar type.
_TEMPLATE_TOKEN_RE = re.compile(r"^\s*\{\{\s*[A-Za-z_][A-Za-z0-9_]*\s*\}\}\s*$")


def _is_template_token(value: Any) -> bool:
    return isinstance(value, str) and bool(_TEMPLATE_TOKEN_RE.match(value))


@lru_cache(maxsize=None)
def _load_schema(kind: str) -> Optional[dict]:
    """Return the vendored JSON Schema for ``kind``, or ``None`` if none exists.

    Result is cached; a missing or unreadable schema file degrades gracefully to
    ``None`` (floor-only validation) rather than raising — DTB principle #4, no
    increment turns a config write into a 500.
    """

    path = _SCHEMA_DIR / f"{kind}.schema.json"
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


@lru_cache(maxsize=None)
def _validator_for(kind: str):
    """Build (and cache) a Draft 2020-12 validator for ``kind`` (or ``None``)."""

    from jsonschema import Draft202012Validator

    schema = _load_schema(kind)
    if schema is None:
        return None

    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_widget_config(kind: str, config: Any) -> None:
    """Validate ``widget_kind`` + ``widget_config``.

    No-op when ``kind`` is blank (the subpart simply has no widget). Enforces the
    universal floor, then — when the kind has a vendored schema — the kind's full
    JSON Schema. Raises ``rest_framework.serializers.ValidationError`` so it
    surfaces as ``400`` through the API.
    """

    if not kind:
        return

    if kind not in KNOWN_WIDGET_KINDS:
        raise serializers.ValidationError(
            {"widget_kind": (f"Unknown widget kind {kind!r}. Known kinds: " f"{sorted(KNOWN_WIDGET_KINDS)}.")}
        )

    if not isinstance(config, dict):
        raise serializers.ValidationError({"widget_config": "widget_config must be a JSON object (dict)."})

    validator = _validator_for(kind)
    if validator is None:
        # Known kind without a vendored schema (e.g. studio-scene): floor only.
        return

    # A value that is nothing but a single ``{{token}}`` is a deferred croupier
    # binding whose concrete value isn't known until per-student substitution, so
    # its value-level error (``type``/``enum``) is dropped. jsonschema's bounds
    # keywords (minimum, exclusiveMinimum, …) already skip non-number instances,
    # so a token never trips those. Structural errors (``additionalProperties``,
    # ``required``) are raised on the parent object, not the token, so a
    # token-bound field must still be a declared field of the kind.
    errors = [err for err in validator.iter_errors(config) if not _is_template_token(err.instance)]
    if errors:
        errors.sort(key=lambda e: list(e.path))
        messages = [_format_error(kind, err) for err in errors]
        raise serializers.ValidationError({"widget_config": messages})


def _format_error(kind: str, err) -> str:  # noqa: ANN001 - jsonschema ValidationError
    """Render a jsonschema error as a teacher-readable, field-scoped message."""

    location = "/".join(str(p) for p in err.path)
    where = f"{kind} config" if not location else f"{kind} config field '{location}'"
    return f"{where}: {err.message}"
