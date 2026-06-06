# 2026-06-05 — IW-9-backend · `TeacherWidget` model scaffold

## Summary

Model-only slice of [IW-9](../initiatives/interactive-widgets-framework.md)
(the **Widget Studio** — Tier 2 of the three-tier authoring model). Ships the
`TeacherWidget` table + admin + tests; **no DRF endpoints**, **no serializer**.

Shipping the table now — independently of IW-1, IW-2, and the rest of the
Studio runtime — is a cheap, low-risk migration that lets the Studio PR start
from *"wire endpoints + UI"* rather than *"design the schema while also
shipping a visual builder"*.

## Classification

**New.** Legacy had no teacher-composed interactive content at all.

## What changed

- **`apps/core/models.py`** — `TeacherWidgetVisibility` enum
  (`personal` / `school` / `pending_review`) + `TeacherWidget` model:
  - `name`, `description`
  - `school` (FK, nullable — open / unaffiliated teachers can own personal
    widgets)
  - `created_by` (FK → User, role-limited to `teacher`)
  - `visibility` (default `personal`)
  - `scene_version` (default 1) + `scene` JSONField — pure-data Studio
    composition (`{primitives, bindings, formulas}`); interpreted by the
    runtime, never `eval`'d.
  - `created_at` / `updated_at`; ordering by `-updated_at`; indexes on
    `(school, visibility)` and `(created_by, updated_at)`.
- **`apps/core/admin.py`** — registered with sensible `list_display` +
  filters + `raw_id_fields`.
- **Migration** `0018_teacherwidget.py` — table-only add, no FK churn.
- **Tests** `apps/core/tests/test_teacher_widget_model.py` (4 cases):
  create with school, personal widget without school, visibility choices,
  ordering by `-updated_at`.

## Migration notes

Adds one table. No data backfill, no schema changes elsewhere. Safe to deploy
ahead of the Studio UI.

## Tests

- `pytest openshiksha/apps/core/tests/test_teacher_widget_model.py` — 4 passed.

## Next

- **IW-9 (full)** — DRF endpoints + serializer + scene-schema validation +
  Studio UI primitives + visual builder. PR 3 here is the schema head start
  for that work.
- **IW-10** — the Studio runtime that interprets the `scene` payload inside
  the same sandbox every other widget uses.
