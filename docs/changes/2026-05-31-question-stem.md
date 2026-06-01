# 2026-05-31 — Question.stem_text (M7-07)

## Summary

Adds an optional `Question.stem_text` shared between subparts. The Cabinet
importer now detects when every subpart of a compound question begins with the
same leading paragraph (a "Read this passage / Consider this figure" shared
stem) and lifts it into `stem_text`, leaving each subpart's `question_text`
holding only the per-part prompt. The student `<QuestionCard />` renders the
stem once above the subpart list.

## Classification

**Improve** — restores legacy Cabinet's shared-stem semantics in a forward-
compatible way (the field is optional and defaults to empty, so every existing
hand-authored question keeps working unchanged).

## Files touched

- `apps/core/models.py` — new `Question.stem_text = TextField(blank=True,
  default="")`.
- `apps/core/migrations/0013_question_stem_text.py` — generated.
- `apps/core/management/commands/import_cabinet_questions.py` — new
  `_split_leading_paragraph` and `_lift_shared_stem` helpers; importer lifts
  the stem when all subparts share it (≥20 chars, ≥2 subparts) and stores it
  on the Question; importer summary now reports `stems=N`.
- `apps/api/serializers/core.py` — `stem_text` exposed on
  `QuestionWithSubpartsStudentSerializer` and `QuestionSerializer`.
- `frontend_modern/src/types/index.ts` — `Question.stem_text?: string`.
- `frontend_modern/src/features/student/QuestionCard.tsx` — renders the stem
  via `<RichContent />` in a warm `ink-50` card above the subpart list.
- `apps/core/tests/test_question_stem.py` — 10 tests covering the leading-
  paragraph split (HTML `<p>`, double-newline, leading whitespace, empty
  input) and the lift logic (single subpart never lifts, identical HTML
  paragraph lifts, differing heads don't lift, short stems below the 20-char
  threshold don't lift, no-paragraph case).

## Why a 20-char threshold

Cabinet content sometimes uses a tiny `<p>Q.</p>` or `<p>(a)</p>` label as the
leading paragraph of every subpart. Those are part-numbering, not a shared
stem — lifting them would strip the only signal the student has that a part
exists. 20 characters reliably skips labels while keeping any real stem.

## Tests

- `pytest apps/core/tests/test_question_stem.py` → 10 passing.
- `pytest apps/core/tests/test_import_cabinet.py` → 31 still passing (no
  regressions on existing importer tests).
- `npm run type-check`, `npm run lint`, `npm run build` clean.
- Django `check` clean.

## Migration notes

Additive nullable text field with empty default — no data backfill required;
existing rows get `""` and the frontend skips rendering when empty.

## Next steps

- M7-05 tag-collision fix + re-import (the import will repopulate `stem_text`
  for any newly-recovered questions).
- M7-03 per-subpart type + grader dispatch.
