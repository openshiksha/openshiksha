# 2026-05-31 — Taxonomy name inference command (M7-09)

## Summary

New `infer_taxonomy_names` Django management command. Renames the 55
`Imported Subject %` / `Imported Chapter %` placeholders left behind by the
Cabinet importer to canonical NCERT-style names, inferred from each chapter's
concept tags + question/solution text against a checked-in NCERT table-of-
contents JSON.

## Classification

**New** — separate from the importer (`import_cabinet_questions.py` stays
deterministic; this command runs after import and is idempotent).

## Files added

- `backend/openshiksha/apps/core/management/commands/infer_taxonomy_names.py`
- `backend/openshiksha/apps/core/data/ncert_toc.json` — NCERT chapter list for
  standards 7–11, Mathematics + Science + Physics + Chemistry, plus a
  `subjects` map from `Imported Subject N` → canonical name (Cabinet subject
  IDs 1–5 are stable across the corpus).
- `backend/openshiksha/apps/core/data/__init__.py` (empty marker)
- `backend/openshiksha/apps/core/tests/test_infer_taxonomy.py` — 12 tests
  covering the tokenizer, candidate-token singularisation, dry-run vs. apply,
  unmatched-skip, idempotency on human-named chapters, and subject renaming.

## How it works

1. **Tokeniser** strips LaTeX (`$…$`, `\(…\)`, `\[…\]`, `\command{…}`,
   `{{var}}`, raw HTML), drops stopwords, keeps `[a-zA-Z][a-zA-Z-]{2,}`.
2. **Keyword bag** per chapter aggregates concept-typed `QuestionTag` names +
   tokens from every subpart's `question_text` + `solution_text`.
3. **NCERT match**: for each placeholder Chapter, look up
   `(standard, subject)` in `ncert_toc.json` → score each candidate chapter
   name by token-overlap count (with trailing-`s` singularisation). Pick the
   top candidate above `--min-score` (default 2); skip on tie.
4. **Subject renaming** is direct from the `subjects` map.
5. **Idempotent**: the regex `^Imported Subject\b` / `^Imported Chapter\b`
   guards against re-touching human-edited names; collision with an existing
   name under the same `(subject, standard)` skips with a warning.
6. **Audit log**: writes `apps/core/data/inferred_taxonomy_<date>.json`
   capturing the proposed rename, reason code (`match`/`tie`/`low-score`/
   `no-toc-entry`), top-3 scores, and applied flag.

## Flags

- `--dry-run` — print rename map, write nothing.
- `--apply` — persist the renames.
- `--min-score N` (default 2) — minimum keyword-overlap score to accept.

Exactly one of `--dry-run` / `--apply` is required (no default action).

## Tests

`pytest openshiksha/apps/core/tests/test_infer_taxonomy.py` → 12 passing.
Django `check` clean.

## Next steps

- M7-07 shared stem (next PR).
- M7-05 tag-collision fix + re-import.
- M7-03 per-subpart type.
- After M7-05's re-import recovers the 33 missing questions, re-run this
  command with `--apply` to backfill any new placeholders.
