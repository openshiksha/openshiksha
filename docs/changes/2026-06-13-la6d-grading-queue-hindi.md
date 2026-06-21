# LA-6d — AI grading queue in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-6)

## Summary

The teacher **AI grading queue** (`OpenResponseGradingPage.tsx`) — the
open-response review surface where the AI proposes a score/feedback/criterion
breakdown and the teacher accepts or overrides it — now renders in the reader's
`preferred_language`. Fourth slice of LA-6, stacked on 6c (shared locale files).

## What changed and why

- `OpenResponseGradingPage.tsx` — every hardcoded string → `t(...)` across all
  four submission statuses (pending / ai_graded / reviewed / failed), the review
  form (final-marks + comment inputs, save/accept buttons, error + lock notes),
  the class/status filters, the load-error retry, and both empty states. The
  module-level `ReviewForm` and `GradeCard` call `useT()` themselves.
- Two module-level constant maps were converted from English-string values to
  `LocaleKey` values and translated at render: `STATUS_LABEL` → `STATUS_KEY`,
  and `FILTER_CHIPS[].label` → `FILTER_CHIPS[].labelKey`. This keeps the lookup
  tables outside the component while still localizing.
- `locales/en.ts` + `locales/hi.ts` — new `grading.*` namespace; reuses
  `teacher.tryAgain`. Score lines interpolate `{score}/{max}` and `{pct}`.

## Conventions / decisions

- `RecordResponsePanel` (rendered inside this page) is **not** localized here —
  it's a separate ~350-line component and gets its own slice (LA-6e) to keep
  this PR atomic.
- `formatDate` still uses the `en-IN` numeric/short-month format; date-locale
  switching is a cross-cutting concern already tracked for the i18n module and
  out of scope for this string pass.
- Hindi strings are genuine domain translations (समीक्षा चाहिए, अंतिम अंक,
  स्वतः जाँचा …).

## Tests

- `type-check` ✅ (key parity) · `lint` ✅
- `vitest OpenResponseGradingPage` — 23 ✅ · `vitest src/shared/i18n` — 13 ✅
- `build` ✅ — entry 122.82 kB (within 160 kB budget)

## Next steps

- **LA-6e** — `RecordResponsePanel.tsx` (record-a-response form on this page).
- `CreateQuestionPage.tsx` (1131 lines) remains its own slice.
- After those, LA-6 reaches Definition of Done and Language Access closes.
