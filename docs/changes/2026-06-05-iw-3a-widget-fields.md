# 2026-06-05 — IW-3a · `widget_kind` + `widget_config` on `QuestionSubpart`

## Summary

Adds the **backend data model** half of the [Interactive Widgets
Framework](../initiatives/interactive-widgets-framework.md) initiative. Every
question subpart can now name a registry-key widget (`widget_kind`) and carry a
typed config (`widget_config`). A small server-side registry guard rejects
unknown kinds at write time so bad authoring payloads never reach the DB.

This PR is the **independent backend keystone** of the
[2026-06-05 batch 2 plan](../daily-plans/2026-06-05-plan-2.md) — it does **not**
depend on IW-1 (the SDK runtime). The moment IW-1 + IW-2 ship, the existing
thermo question can flip from `interactive_html` to `widget_kind="thermo-piston"`
without further schema work.

## Classification

**New.** Legacy had no analogue: interactive content was a one-off raw HTML
blob; there was no typed widget contract.

## What changed

- **`apps/core/models.py`** — `QuestionSubpart` gets `widget_kind: CharField`
  (blank = no widget) and `widget_config: JSONField` (defaults `{}`). Both
  additive, both nullable-equivalent — zero-downtime migration.
- **`apps/core/widgets.py`** — new module. `KNOWN_WIDGET_KINDS` set + a
  `validate_widget_config(kind, config)` floor that enforces (a) blank or known
  kind, (b) config is a JSON object. Per-kind JSON-Schema validation hangs off
  the same module as widgets ship in IW-2 / IW-4 / IW-6.
- **`apps/core/admin.py`** — both fields surfaced on the subpart inline.
- **`apps/api/serializers/core.py`** — exposed on the teacher full serializer,
  the student-safe serializer, and the writable serializer. The writable
  serializer's `validate()` calls the kind guard so unknown kinds become
  `400 Bad Request`.
- **Migration** `0018_questionsubpart_widget_config_and_more.py`.
- **Tests** `apps/core/tests/test_widget_fields.py` — 10 cases covering field
  round-trip, defaults, the validator's three branches, and the API surface
  (create with widget, reject unknown kind, reject non-dict config, blank kind
  passes).

## Legacy reference

None — modern-only.

## Migration notes

Both fields default to safe empty values, so existing rows pick them up with no
data backfill required. The legacy `is_interactive` / `interactive_html` path
(M7-11, #132) stays untouched and continues to render correctly.

## Tests

`pytest openshiksha/` — 830 passed.

## Next

- **IW-3b** (next PR in this run) — `migrate_legacy_thermo_widget` management
  command + per-student `{{var}}` substitution into `widget_config` in the
  student serializer.
- **IW-2** (later, gated on IW-1) — `defineWidget()` factory + `thermo-piston`
  React widget; once it ships the legacy thermo question can flip onto the new
  kind-based path.
