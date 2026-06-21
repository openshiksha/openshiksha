# LA-6c — build-problem-set page in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-6)

## Summary

The teacher **Build Problem Set** flow (`CreateProblemSetPage.tsx`) — the details
card, the two-pane question picker (with search / difficulty / type filters), the
selected-questions strip, the live question preview, and the desktop + sticky
mobile submit bars — now renders in the reader's `preferred_language`. Third slice
of LA-6, stacked on 6b (shared locale files).

## What changed and why

- `CreateProblemSetPage.tsx` — every hardcoded string → `t(...)`, including
  `aria-label`s (`Select question {id}`, `Remove question {id}`) and `title`
  attributes (`Difficulty {n}/5`). The module-level sub-components `QuestionRow`
  and `SelectedStrip` call `useT()` themselves; `FilterChip` has no own copy.
  Renamed a shadowing `availableTypes.map((t) => …)` param to `qType` so the
  translate function `t` stays in scope (and to keep `no-shadow` clean).
- `locales/en.ts` + `locales/hi.ts` — new `setForm.*` namespace. Reused
  `assignForm.eyebrow` / `assignForm.back` / `assignForm.createFailed` /
  `assignForm.backToDashboard` and `teacher.titleLabel` rather than duplicating.

## Conventions / decisions

- Same plural pattern (`*One`/`*Many` selected by the component) and
  whole-sentence interpolation as 6a/6b (success body recomposed from its
  previous `<strong>`-fragmented form).
- The mobile button keeps its numeric `(N)` suffix appended outside the
  translated `setForm.createMobile` label, since that count is a live control
  affordance, not prose.
- Hindi strings are genuine domain translations (प्रॉब्लम सेट, अध्याय, कठिनाई,
  सेट में जोड़ें …).

## Tests

- `type-check` ✅ (key parity) · `lint` ✅
- `vitest CreateProblemSetPage` ✅ · `vitest src/shared/i18n` — 13 ✅
- `build` ✅ — entry 120.60 kB (within 160 kB budget)

## Next steps

- **LA-6d** — AI grading queue (`OpenResponseGradingPage` + `RecordResponsePanel`).
- `CreateQuestionPage.tsx` (1131 lines) remains its own slice.
- After those, LA-6 reaches Definition of Done and the Language Access
  initiative closes.
