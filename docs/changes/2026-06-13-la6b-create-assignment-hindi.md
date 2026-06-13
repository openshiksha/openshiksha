# LA-6b — create-assignment page in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-6)

## Summary

The teacher **Create Assignment** flow (`CreateAssignmentPage.tsx`) — the
three-step authoring form plus its live student-facing preview — now renders in
the reader's `preferred_language`. Second slice of LA-6 (after 6a, the dashboard
panels). Stacked on the 6a branch because both touch the shared locale files.

## What changed and why

- `CreateAssignmentPage.tsx` — replaced every hardcoded English string with
  `t(...)`: the section header, the three step cards (choose class / pick
  problem set / set due date), quick-set date presets, the success state, and
  the whole `AssignmentPreview` panel (hero strip, "what students will see",
  due strip, recipients, action footer) plus the sticky mobile publish bar.
  The two module-level sub-components (`ProblemSetRow`, `AssignmentPreview`)
  call `useT()` themselves.
- `locales/en.ts` + `locales/hi.ts` — new `assignForm.*` namespace. Reused the
  existing `teacher.questionsCount{One,Many}`, `teacher.studentsCount{One,Many}`
  and `teacher.minutesApprox` keys rather than duplicating them.

## Conventions / decisions

- **Pluralization** follows the established LA pattern — singular/plural `*One`
  / `*Many` key pairs selected by the component (`count === 1 ? … : …`), since
  the in-house `t` is string-only (no ICU plural).
- **Due-date sentences** (which previously embedded `<strong>` mid-sentence and
  branched on today / N-days-from-now) were recomposed as whole interpolated
  strings so Hindi word order is natural and translation-complete — no
  fragment-by-fragment concatenation.
- Hindi strings are genuine domain translations (प्रॉब्लम सेट, अंतिम तिथि,
  प्रकाशित करें …).

## Tests

- `type-check` ✅ (proves en↔hi key parity) · `lint` ✅
- `vitest CreateAssignmentPage` ✅ · `vitest src/shared/i18n` — 13 ✅
- `build` ✅ — entry 118.36 kB (within 160 kB budget)

## Next steps

- **LA-6c** — `CreateProblemSetPage.tsx`.
- **LA-6d** — AI grading queue (`OpenResponseGradingPage` + `RecordResponsePanel`).
- `CreateQuestionPage.tsx` (1131 lines) is a slice of its own.
