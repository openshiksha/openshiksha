# 2026-05-31 — Cabinet tag collision fix (M7-05)

## Summary

Scope the Cabinet importer tag by chapter so questions that share a raw
`question_id` across different chapter folders no longer collapse into a single
row. The legacy tag `cabinet:<question_id>` collided across 33 questions; the
new tag `cabinet:c<chapter_id>:q<question_id>` is unique per imported Question.

A reversible data migration rewrites every existing legacy tag to the new
form, joining via the first attached Question's chapter FK. After the
migration lands, re-running the importer recovers the previously-dropped 33
questions as fresh rows (their tags are now in chapter folders the old
collision had hidden).

## Classification

**Improve** — tag-naming convention change + idempotent data migration.

## Files touched

- `apps/core/management/commands/import_cabinet_questions.py` — tag format
  updated to `cabinet:c{chapter.id}:q{question_id}` with an explanatory
  comment pointing at the collision case.
- `apps/core/migrations/0013_cabinet_tag_path.py` — `RunPython` data migration
  with both forward (`cabinet:<N>` → `cabinet:c<chapter_id>:q<N>`) and reverse
  (round-trip back) functions. Skips orphan tags (no attached Question) and
  collision targets (existing scoped tag). Logs counts via stdout.
- `apps/core/tests/test_import_cabinet.py` — existing 4 lookups that used the
  legacy `cabinet:1001` form now use `name__endswith=":q1001"`; new
  `test_tags_are_chapter_scoped` asserts every cabinet tag has the new shape
  and is attached to exactly one Question.
- `apps/core/tests/test_cabinet_tag_migration.py` — 3 migration tests using
  `MigrationExecutor` to run the migration forward / backward / forward-on-
  orphan against a real test DB.

## What changed and why

- The legacy importer used only the raw question-file basename (`1.json` →
  `cabinet:1`). The same basename appears in dozens of chapter folders in the
  Cabinet repo, so `get_or_create` returned the same tag on every import,
  collapsing distinct questions into one row.
- The new tag includes the modern `Chapter.pk` (always unique). Using a
  modern FK rather than the legacy `<board>/<school>/<standard>/<subject>/
  <chapter>` path keeps the tag short and stable across re-imports (the same
  chapter row is reused).
- The migration is forward + reverse safe; logs `rewrote / skipped_orphan /
  skipped_collision` counts so production rollouts have an audit trail.

## Tests

- `pytest apps/core/tests/test_import_cabinet.py` → 32 passing.
- `pytest apps/core/tests/test_cabinet_tag_migration.py` → 3 passing.
- `pytest apps/core/tests/` (full core suite) → 177 passing.
- Django `check` clean.

## Migration notes

Run order on prod: `manage.py migrate core 0013_cabinet_tag_path` (rewrites
tags), then `manage.py import_cabinet_questions --source <repo>` (re-imports;
formerly-collided 33 questions land as new rows).

## Next steps

- M7-03 per-subpart type + grader dispatch (final PR in this batch).
- After import, re-run `infer_taxonomy_names --apply` if the import created
  new placeholder chapters/subjects.
