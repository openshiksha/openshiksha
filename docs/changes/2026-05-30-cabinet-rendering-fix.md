# Cabinet rendering fix (M7-02)

**Date**: 2026-05-30
**Classification**: Fix + Improve
**Branch**: `fix/2026-05-30-cabinet-rendering` (based on `modernization`)

## Summary

After M7-01 (`RichContent`) shipped, real-content inspection as
`student_demo` revealed that the imported Cabinet bank rendered with
broken variable substitution everywhere, no images, and several
unsupported expression helpers. This change fixes the importer's
brace-stripping bug, teaches croupier to evaluate expression tokens
(`{{2*k}}`, `{{trunc(pi_val*r*r, 2)}}`), substitutes variables in
worked-out solutions and hints, and discovers Cabinet image siblings —
then re-imports the whole bank against the local cabinet clone.

This is **M7-02 — Question variable substitution** in the V2
initiative ledger.

## Before / After (1734 imported subparts)

| Metric | Before | After |
|---|---:|---:|
| Proper `{{expr}}` substitution tokens | 0 (all broken to single brace) | **3308** |
| True single-brace expression remnants | 751 | **0** (171 remaining are genuine LaTeX `\frac{a}{b}`, not template tokens) |
| Subparts with `image_url` populated | 0 | **137** |
| Worked solutions / hints showing `{{var}}` to the student | 904 | **0** |
| `trunc`/`Decimal`/`pi_val` evaluation | unsupported | supported |

## Root causes

1. **Importer dropped a brace pair**: `_EXPR_TOKEN` was
   `r"_\{(\{[^{}]+\})\}_"` with replacement `r"\1"`, so Cabinet
   `_{{4*k}}_` became `{4*k}` (single braces). Modern croupier only
   recognises `{{...}}`, so 751 expression tokens leaked to display.
2. **Solutions/hints never substituted**:
   `QuestionSubpartStudentSerializer` only applied substitution to
   `question_text` + `options`. So worked solutions displayed
   `r = {{k}}` instead of `r = 4`.
3. **`safe_eval_expr` allowlist too narrow**: it covered only
   `+ - * / **`. Cabinet authors freely used `trunc(...)`,
   `Decimal(...)`, `pi_val`, `sqrt`, `floor`, `ceil`, etc.
4. **Images never discovered**: the importer never scanned the cabinet
   for sibling/img-subdir image files.

## What changed

### `backend/openshiksha/apps/api/croupier.py`
- `substitute_variables` now finds every `{{...}}` token and either
  resolves it as a bare identifier or evaluates it as an expression
  via the safe AST evaluator. Tokens that fail to evaluate are left
  intact rather than raising, so one bad expression never blanks a
  whole question.
- `safe_eval_expr` gained an allowlist of safe helpers
  (`trunc, round, abs, min, max, sqrt, floor, ceil, Decimal, int,
  float, pow`) and constants (`pi_val, e_val`). Anything outside the
  list still raises (the existing security tests stay green).
- Output formatting trims trailing zeros so floats display as
  `28.27` not `28.2700`.

### `backend/openshiksha/apps/core/management/commands/import_cabinet_questions.py`
- `_EXPR_TOKEN` now correctly emits `{{expr}}` (double braces).
- `_find_subpart_image` discovers cabinet images in both layouts
  (sibling-to-JSON and `img/` subdirectory) and attaches a
  `raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/...`
  URL on the imported subpart.
- Stats output now reports `images=N`.

### `backend/openshiksha/apps/api/serializers/core.py`
- `QuestionSubpartStudentSerializer.to_representation` reuses the
  per-student sampled values from
  `substitute_variables_for_student` to also substitute
  `solution_text` and `hint_text`. Solutions and hints stay coherent
  with what the student sees in the question body.

### Tests
- `apps/core/tests/test_croupier_phase2.py`: 13 new assertions —
  bare-identifier substitution, expression evaluation,
  `trunc` / `pi_val` / `Decimal` / `sqrt` / unknown-fn rejection,
  graceful fallback on bad tokens.
- `apps/core/tests/test_import_cabinet.py`: existing
  `test_expression_token_keeps_inner_braces` was asserting the buggy
  behaviour and is now `test_expression_token_becomes_modern_double_brace`.
  Added explicit `_{{2*k}}_` and `_{{trunc(pi_val*r*r,2)}}_`
  conversion cases, plus image discovery in both layouts.
- New `apps/api/tests/test_subpart_substitution.py` (6 tests):
  end-to-end verification that solutions, hints, and question bodies
  substitute with the same per-student seeded values.

Full suite: **620/620 passing**.

## Re-import

Bind-mount the local cabinet clone via a gitignored
`docker-compose.override.yml`, then:

```bash
docker compose exec backend python manage.py import_cabinet_questions \
  --source /cabinet/questions
```

Output: `imported=0 updated=646 skipped=2 new_subjects=4 new_chapters=51 images=137`.

## How to verify

1. `docker compose up -d` (the new override.yml mounts the cabinet clone).
2. Log in as `student_demo` / `demo1234`.
3. Open the medicine-capsule question (Q652). Confirm:
   - Question body shows actual numbers, e.g. `diameter is 8cm`, not
     `diameter is {2*k}cm`.
   - "Show worked solution" shows fully-substituted prose, e.g.
     `r = 4` and `2 × π × 4 × 4 = 100.53`, not `r = {{k}}` and
     `{trunc(2*pi_val*k*k,2)}`.
   - Diagrams render where the cabinet repo has them.

## Migration / data notes

No new Django migrations — all fields exist already (`image_url`,
`solution_text`, `hint_text` were added in earlier PRs). Existing rows
healed in place by the re-import (subparts are replaced wholesale by
the importer's existing transactional flow).

## Follow-ups

- 171 single-brace patterns remain in the corpus, all genuine LaTeX
  fractions (`\frac{j*k+1}{k}`). Not a bug — these are typeset by
  KaTeX via the M7-01 `RichContent` renderer.
- Cabinet question-id tags collide across chapters (33 of 679
  questions weren't updated because their `cabinet:<id>` tag matches
  multiple containers). Worth a follow-up — make the tag include
  `subject_id/chapter_id` for uniqueness.
- Some legacy expressions reference helpers we don't yet allowlist —
  surfaced graceful (token left intact), but worth a `--report-unknowns`
  flag on the importer for triage.
