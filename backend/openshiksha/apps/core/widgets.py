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


# ─────────────────────────────────────────────────────────────────────────────
# AI authoring support (DTB-2)
#
# The kinds the Describe-to-Build AI may author, the deterministic safe-default
# config for each (the fallback when an LLM is unavailable or its output cannot
# be salvaged), and a deterministic repair pass that clamps/drops an LLM-proposed
# config toward its kind's schema. None of this calls an LLM — it is the
# deterministic guardrail that AI authoring rides on (initiative principles
# #3 validate-before-store and #4 deterministic fallback).
# ─────────────────────────────────────────────────────────────────────────────

# AI authors *config-as-data* for these answer-producing / explanatory kinds
# only. ``custom-html`` is excluded on purpose — it carries author HTML (code,
# not data) and is admin-gated — and ``studio-scene`` has no vendored schema to
# validate against, so neither is a safe AI target.
AI_AUTHORABLE_WIDGET_KINDS: tuple[str, ...] = (
    "number-line",
    "fraction-bar",
    "function-plotter",
    "thermo-piston",
)

# Deterministic, schema-valid default config per authorable kind. Used as the
# fallback when no LLM provider is available or its output cannot be repaired —
# always a working widget, never a 500 and never stub text shown as a real
# generation (the caller flags provenance honestly).
SAFE_DEFAULT_CONFIGS: dict[str, dict] = {
    "number-line": {"min": 0, "max": 10, "step": 1, "label": "Mark the value"},
    "fraction-bar": {"numerator": 1, "denominator": 4, "mode": "shaded"},
    "function-plotter": {"expr": "x**2", "xMin": -5, "xMax": 5, "yMin": -5, "yMax": 5},
    "thermo-piston": {},
}

# Sentinel for "this value could not be coerced and must be dropped".
_DROP = object()


def get_widget_schema(kind: str) -> Optional[dict]:
    """Public accessor for a kind's vendored JSON Schema (or ``None``)."""

    return _load_schema(kind)


def is_valid_widget_config(kind: str, config: Any) -> bool:
    """Boolean form of :func:`validate_widget_config` (never raises)."""

    try:
        validate_widget_config(kind, config)
        return True
    except serializers.ValidationError:
        return False


def _coerce_value(spec: dict, value: Any) -> Any:
    """Deterministically coerce one field value toward its schema, or ``_DROP``.

    Clamps numbers into ``minimum``/``maximum``/``exclusiveMinimum`` bounds, keeps
    only enum members for enum fields, and keeps strings for string fields.
    Anything that cannot be salvaged returns the ``_DROP`` sentinel so the caller
    omits the field (every field on the authorable kinds is optional).
    """

    enum = spec.get("enum")
    if enum is not None:
        return value if value in enum else _DROP

    declared = spec.get("type")
    if declared == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return _DROP
        result: float = value
        if "minimum" in spec:
            result = max(result, spec["minimum"])
        if "maximum" in spec:
            result = min(result, spec["maximum"])
        if "exclusiveMinimum" in spec and result <= spec["exclusiveMinimum"]:
            # Cannot represent "just above" the bound deterministically — fall to
            # the schema's own default when it satisfies the bound, else drop.
            default = spec.get("default")
            if isinstance(default, (int, float)) and default > spec["exclusiveMinimum"]:
                return default
            return _DROP
        return result
    if declared == "string":
        return value if isinstance(value, str) else _DROP
    return value


def repair_widget_config(kind: str, raw_config: Any) -> dict:
    """Best-effort deterministic coercion of an LLM-proposed config.

    Drops unknown keys (``additionalProperties: false``), clamps numeric bounds,
    and removes invalid enum values. ``{{token}}`` bindings are passed through
    untouched (DTB-5 croupier tolerance). The result is *not guaranteed* valid —
    the caller must still run :func:`is_valid_widget_config` and fall back to
    :data:`SAFE_DEFAULT_CONFIGS` when repair cannot produce a valid config.
    """

    schema = get_widget_schema(kind)
    if schema is None or not isinstance(raw_config, dict):
        return {}

    props = schema.get("properties", {})
    repaired: dict = {}
    for key, value in raw_config.items():
        if key not in props:
            continue
        if _is_template_token(value):
            repaired[key] = value
            continue
        coerced = _coerce_value(props[key], value)
        if coerced is not _DROP:
            repaired[key] = coerced
    return repaired
