# Cabinet Question Import + Worked Solutions (P8)

**Date**: 2026-05-27
**Classification**: Port + Improve + New
**Branch**: `feat/2026-05-27-cabinet-import` → `modernization`

## Summary

Closes the content gap (P8). Adds the `solution_text`/`hint_text` fields the
legacy Cabinet questions carry, builds the `import_cabinet_questions` management
command that converts the legacy Cabinet JSON bank into the modern DB schema, and
surfaces worked solutions to students after grading. Also wires LLM question
generation to produce a worked solution that lands in `solution_text`.

## Legacy files referenced

- `cabinet/cabinet_api.py` — original live-HTTP fetch of question containers/subparts
- `croupier/constraints.py` (constraint format) — informed the constraint conversion
- modern `backend/openshiksha/apps/api/croupier.py` `safe_eval_expr` — why `pow()` must be rewritten

## What changed from legacy and why

Legacy questions lived in the **Cabinet microservice**, fetched live over HTTP at
render/grade time — a runtime dependency with no offline/seed capability. This work
imports that content **directly into the Django DB** as a one-time migration:

- `_{var}_` / `_{{expr}}_` tokens → modern `{{...}}` (aligns with Croupier)
- `pow(a, b)` → `(a)**(b)` (modern `safe_eval_expr` supports `**`, not `pow()`)
- legacy `{"range": {"include": [[1,6]]}}` constraints → `{"min", "max", "integer"}`
- cabinet `options.correct`/`options.incorrect` → keyed `[{"key": "A", ...}]`
- cabinet types 1/2/3/4 → `mcq`/`multi_select`/`numeric`/`fill_blank`
- `solution`/`hint` → new `solution_text`/`hint_text` fields (legacy dropped these in the modern schema)

**Bonus over legacy**: worked solutions are now shown to students inline after
grading (legacy kept solutions teacher-only in the answer key).

## Technical details

### P8a — fields
- `QuestionSubpart.solution_text` + `hint_text` (`TextField`, `blank`, `default=""`)
- Migration `0011_questionsubpart_solution_hint_text` (additive, zero-risk)
- Admin inline exposes both fields
- Write serializer + full teacher serializer carry both; authoring form (`CreateQuestionPage`) gets two textareas, prepopulated in edit mode
- LLM generation: added a `solution` field to the generation tool schema/prompt/stub and the draft serializer; "Use this draft" maps `solution` → `solution_text`

### P8b — import command
- `import_cabinet_questions.py` with pure, unit-tested converters (`convert_tokens`, `convert_pow`, `convert_constraints`, `convert_options`, `convert_subpart`)
- Flags: `--source` (required), `--mapping`, `--limit`, `--dry-run`
- Idempotent via a `cabinet:<question_id>` special `QuestionTag`; re-import replaces subparts in place
- Placeholder `Imported Subject <id>` / `Imported Chapter <id>` when no `--mapping` given — import never hard-fails on missing taxonomy
- Robust: each container in its own (savepoint) transaction; one malformed question is skipped with a warning, not fatal. `--dry-run` wraps the whole run in one rolled-back transaction
- Synthetic fixtures under `apps/core/tests/fixtures/cabinet_sample/` mirror the real Cabinet layout (the 679-question repo is external; the bulk run is an operational follow-up)

### P8c — student display
- `QuestionSubpartStudentSerializer` includes `hint_text` always and `solution_text`
  only when `context["include_solutions"]` is set
- `AssignmentViewSet.get_serializer_context` sets that flag only when the student's
  own submission for the assignment is graded (`score` not null) — anti-cheat gate
- `QuestionCard` gains a collapsible "Need a hint?" (during practice) and
  "Show worked solution" (after grading), KaTeX-rendered

## Tests written

- `test_import_cabinet.py` — 27 tests: token/pow/constraint/option/subpart converters + command behavior (dry-run writes nothing, placeholder creation, mapping resolution, malformed skip, idempotent re-import, solution/hint import, token conversion in content, `--limit`)
- `test_question_models.py` — `solution_text`/`hint_text` default empty; student serializer gating (hidden without flag, shown when graded)
- Full backend suite: **472 passed**
- Frontend: type-check, lint, 11 tests, build all pass

## Migration notes

`0011` is additive (`default=""`), safe on existing rows. No data migration.

## Next steps

- Operational: clone `openshiksha-cabinet` locally and run the importer for the
  full 679-question bank, ideally with a `--mapping` file derived from the legacy
  MySQL subject/chapter IDs (placeholders otherwise, reconcilable in admin).
- Nested `pow(pow(...))` converts only the inner call; rare, flagged in tests.
