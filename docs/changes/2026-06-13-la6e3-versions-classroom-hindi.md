# LA-6e-3 — version history & classroom join-code in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** Language Access (2026-language-access.md) — LA-6e (uses LA-8)

## Summary

Localized the **problem-set version-history page** (+ its diff panel) and the
**classroom join-code widget**. Both render absolute timestamps/expiry, so this is
the first 6e slice to consume the LA-8 `formatDate`/`useFormat` helper (now on
`modernization`) — version timestamps render "8 जून 2026, 3:30 pm" in Hindi
instead of a hardcoded `en-IN` string. Chrome strings only.

## Legacy reference

None — legacy Django 1.11 had no teacher i18n and no version history. Pure
"improve".

## What changed

- **`ProblemSetVersionsPage.tsx`** — page title/description, back links, empty
  state, version label + Target/Against badges, question/pinned counts
  (singular/plural), diff helper text, the `DiffPanel` (Diff heading, clear,
  load-error) and `DiffSummary` (added/removed/answer/content lines sing/plural,
  the "Comparing X against Y" line, identical-content). The row timestamp now uses
  **`useFormat().formatDate`** (LA-8) with a date+time `opts` override, replacing
  the hardcoded `toLocaleString('en-IN', …)`.
- **`ClassroomCodeWidget.tsx`** — heading, copy code/link (+ copied state),
  regenerate confirm dialog (warning, yes/cancel), regenerate/generate buttons,
  and `formatExpiry` (now takes `t`) for the no-expiry / expired / expires-in
  hours/days labels.
- **Locale files** — ~50 new keys in both `en.ts` and `hi.ts` under LA-6e-3
  sections (`psVersions.*`, `classCode.*`). Glossary register: संस्करण, क्लासरूम
  जॉइन कोड. Parity guard stays green.

## Tests

- Updated `ProblemSetVersionsPage.test.tsx` (the diff line wording moved from
  `answer(s) changed` to proper singular `answer changed`) + a renders-in-Hindi
  title case.
- Added a renders-in-Hindi case to `ClassroomCodeWidget.test.tsx` (heading +
  no-expiry label).
- Full suite green: 58 files / 371 tests. Lint + tsc clean. Build under budget
  (entry 130 kB).

## Next steps

LA-6e-4 — `CreateQuestionPage` (the last English-only teacher surface), which
closes LA-6.
