"""
Server-side source of truth for the Interactive Widgets Framework registry.

The frontend SDK (``frontend_modern/src/widgets/registry.ts``) is where each
widget is wired into the runtime. This module mirrors the *names* the backend
will accept so authoring endpoints can reject typos at write time and per-kind
JSON-Schema validation can hang off the same map as widgets land.

Per-kind ``params.schema.json`` validation is added per widget in
IW-2 / IW-4 / IW-6. For IW-3a we only enforce the two universal contracts:

    1. ``widget_kind`` must be either blank or a known registry key.
    2. ``widget_config`` must be a dict (JSON object).

That floor is enough to keep bad authoring payloads out of the DB without
blocking widgets that haven't shipped their schema yet.
"""

from __future__ import annotations

from typing import Any

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


def validate_widget_config(kind: str, config: Any) -> None:
    """Validate ``widget_kind`` + ``widget_config`` at the universal floor.

    No-op when ``kind`` is blank (the subpart simply has no widget). Raises
    ``rest_framework.serializers.ValidationError`` so it surfaces as ``400``
    through the API.
    """

    if not kind:
        return

    if kind not in KNOWN_WIDGET_KINDS:
        raise serializers.ValidationError(
            {"widget_kind": (f"Unknown widget kind {kind!r}. Known kinds: " f"{sorted(KNOWN_WIDGET_KINDS)}.")}
        )

    if not isinstance(config, dict):
        raise serializers.ValidationError({"widget_config": "widget_config must be a JSON object (dict)."})
