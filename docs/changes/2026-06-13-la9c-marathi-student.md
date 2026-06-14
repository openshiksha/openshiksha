# LA-9c — Marathi student core loop

**Date:** 2026-06-13
**Classification:** New (content)
**Initiative:** Language Access — depends on LA-9b (#350)

## Summary

Extends the Marathi pilot dictionary (`locales/mr.ts`) with the **student core
loop** — dashboard, assignment list/cards, assignment detail + submission flow,
due-for-review (SRS), recommendations, AI-explanation chrome, and the activity
streak (~72 keys). A Marathi student now moves through the daily practice loop
in मराठी, with English fallback only for surfaces not yet translated.

## What changed

- **`locales/mr.ts`** — added the student-loop clusters: `dashboard.` (8),
  `assignments.`/`assignment.` (15), `assignmentDetail.` (14), `dueReview.` (12),
  `recommendations.` (8), `explanation.` (7), `streak.` (8). All placeholders
  (`{name}`, `{distance}`, `{answered}`/`{total}`, `{date}`, `{days}`,
  `{minutes}`, `{count}`) preserved — the parity guard enforces this.
- **`ExplanationPanel.tsx`** — the "re-explain in this language" affordance now
  compares `explanation.language` against `toAiLanguage(locale)` rather than the
  raw locale. A pilot locale (mr) generates explanations in English, so an
  English explanation is already correct and the regenerate button correctly
  does **not** appear (previously it would show perpetually for mr).
- **`explanation.regenerateInLocale` / `.regenerating`** are intentionally left
  untranslated in mr (documented inline) — AI content for mr falls back to
  English, so that affordance never applies.
- **`dateFnsLocale.ts`** — documented that Marathi has **no** date-fns locale in
  date-fns 4.x, so mr *relative* dates fall back to English phrasing while mr
  *absolute* dates still localize via the `Intl` `mr-IN` formatter. (No `mr`
  entry added — the import doesn't exist.)

## Tests

- New `i18n.test.tsx` case: renders Marathi student-loop chrome
  (`dashboard.title` resolves to Marathi, not English).
- Updated the LA-9b fallback case to probe a `teacher.*` key (still outside the
  pilot) since streak is now translated.
- Parity guard's pilot branch stays green with the larger mr subset.
- `tsc` clean · `eslint` clean · `vitest run` → 395 passed · build green
  (`mr-*.js` lazy chunk 10.4 kB).

## Next steps

LA-9d: Marathi parent surface + the **backend** AI/email `mr → en` fallback
guard (this PR + 9b did the frontend clamp only).
