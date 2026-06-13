# LA-8 — locale-aware date/number helper

**Date:** 2026-06-13
**Classification:** Improve / foundation-hardening
**Initiative:** Language Access (2026-language-access.md) — LA-8

## Summary

Added a single `Intl`-backed `formatDate`/`formatNumber` helper so every surface
formats absolute dates and counts the same way for the active locale, instead of
each screen reinventing `toLocaleDateString` with an ad-hoc (often `undefined`)
locale. This is the foundation half that LA-6a–d were meant to consume; it was
skipped in the prior run and is now shipped, so the LA-6e date surfaces (versions,
snapshots, due-date chips) can render "27 मई 2026" through one helper.

## Legacy reference

None — legacy Django 1.11 server-rendered English templates with no `Intl` layer
and no language preference. Pure "improve"; nothing to port.

## What changed

- **New `frontend_modern/src/shared/i18n/format.ts`:**
  - `formatDate(value, locale, opts?)` — `Intl.DateTimeFormat` keyed to
    `hi-IN`/`en-IN`. Default medium day-first style ("27 May 2026" / "27 मई 2026");
    accepts `opts` overrides. Invalid input returned verbatim (never throws).
  - `formatNumber(value, locale, opts?)` — `Intl.NumberFormat` with Indian
    grouping but **Latin numerals** for both locales (deliberate product decision
    for K-12 counts — documented in a code comment, do not "fix" to Devanagari).
  - `useFormat()` hook returning `formatDate`/`formatNumber` bound to the active
    locale, mirroring `useT()`.
  - Exported from `shared/i18n/index.ts`.
- **Swapped the first ad-hoc absolute-date render:**
  `CreateAssignmentPage.formatDueDate` previously called
  `toLocaleDateString(undefined, …)` — i.e. browser default locale, so a
  Hindi-medium teacher saw English dates. Now takes the active `locale` and routes
  through the shared `formatDate`, so all four due-date displays on that page
  localize.

## Why `Intl`, not a dependency

`Intl` is built into every browser — adds nothing to the entry chunk (principle 2,
160 kB budget). Verified: entry chunk stayed at 123 kB after build. For *relative*
dates ("3 दिन में") the LA-3 date-fns `hi` locale is still used; this helper is for
absolute dates and numbers only.

## Tests

- New `format.test.ts` — 8 cases: en/hi medium date, `opts` override,
  invalid-input passthrough (both locales), `Date` instance input, Indian grouping
  with Latin digits (en + hi), non-finite passthrough.
- Full suite green: 58 files / 365 tests. Lint + tsc clean. Build under budget.

## Next steps

PR 4 (LA-6e-3 versions + classroom code) and PR 5 (CreateQuestionPage) consume
`formatDate` for their timestamps. The 6a–d date renders can be back-filled to the
helper opportunistically.
