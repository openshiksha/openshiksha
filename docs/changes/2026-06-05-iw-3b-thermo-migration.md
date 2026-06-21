# 2026-06-05 — IW-3b · legacy-thermo migration + per-student `widget_config` substitution

## Summary

Builds on [IW-3a](2026-06-05-iw-3a-widget-fields.md) by (a) shipping the
one-shot **`migrate_legacy_thermo_widget`** management command that points the
Class-11 Thermodynamics piston question at `widget_kind="thermo-piston"`, and
(b) extending the **per-student `{{var}}` substitution** the croupier already
applies to `question_text` / `options` / `interactive_html` so it also walks
`widget_config` and substitutes tokens in every string leaf.

That means the moment IW-1 + IW-2 land, the thermo question's runtime receives
its `init` payload with already-resolved per-student numbers — no parallel
substitution path, no second token semantics, no chance of drift.

## Classification

**New.** Legacy had no widget-config substitution analogue; the thermo widget
inlined its variables into raw JS.

## What changed

- **`apps/core/management/commands/migrate_legacy_thermo_widget.py`** (new) —
  idempotent stamping of `widget_kind` + `widget_config` on the legacy thermo
  subpart. `--dry-run` and `--subpart-id <id>` flags. Refuses to write when
  more than one match is found and no explicit id is given. Leaves
  `interactive_html` untouched (IW-7 deprecates that field, not this PR).
- **`apps/api/serializers/core.py`** — new internal `_substitute_in_json`
  helper. Reused by `QuestionSubpartStudentSerializer.to_representation` when
  the subpart has `variable_constraints` — walks the JSON tree, substitutes via
  `substitute_variables` on string leaves, passes numbers/bools/None through
  untouched, recurses into nested dicts and lists.
- **`apps/core/tests/test_widget_fields.py`** — three new cases on top of
  IW-3a's 10:
  - JSON substitution into nested string leaves + pass-through for
    non-strings.
  - Migration command stamps the expected kind+config and is idempotent on
    re-run.
  - `--dry-run` writes nothing.

## Legacy reference

- `openshiksha-cabinet/questions/raw/1/1/11/3/44/22.json` — the one and only
  legacy interactive widget.
- `apps/api/croupier.py` — the croupier's `substitute_variables` /
  `substitute_variables_for_student`; reused, not forked.

## Migration notes

The command runs zero rows by default in dev (no thermo subpart imported) and
exactly one row in prod (the Cabinet thermo subpart). It is safe to wire into
the existing import / cabinet pipeline; for now it stays a one-shot the
operator runs explicitly.

## Tests

- `pytest openshiksha/apps/core/tests/test_widget_fields.py` — 13 passed.

## Next

- **IW-9-backend** (next PR this run) — `TeacherWidget` model scaffold.
- **IW-2** (later, gated on IW-1) — `thermo-piston` React widget. Once that
  ships the legacy `interactive_html` path can be cut over (IW-7).
