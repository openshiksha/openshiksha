# LA-3 — student core-loop chrome in Hindi

**Date:** 2026-06-11
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-3)

## Summary

The entire student core loop now renders in Hindi when the locale is `hi`:
dashboard (greeting, panels, empty/error states), assignment list (sections,
card status labels, CTAs), assignment detail (progress line, score banner,
submit flow + confirm dialog), Due-for-Review panel, Recommendations panel,
and the streak badge. Chrome only — authored content (question text, titles,
chapter/subject names) renders as authored, per initiative principle 1.

## Legacy files referenced

None — legacy was English-only.

## What changed and why

- **~60 new keys** in `locales/en.ts` / `locales/hi.ts` across namespaces
  `dashboard.*`, `assignments.*`, `assignment.*`, `assignmentDetail.*`,
  `dueReview.*`, `recommendations.*`, `streak.*`, plus `common.cancel/practice/
  topics*`. Key parity remains tsc-enforced (`LocaleDict`).
- **Components migrated to `t()`** (string extraction only, zero behavior
  change): `StudentDashboard`, `AssignmentList`, `AssignmentCard`,
  `AssignmentDetailPage`, `DueForReviewPanel`, `RecommendationsPanel`,
  `StreakBadge`.
- **Relative dates localize too**: new `shared/i18n/dateFnsLocale.ts` maps the
  active locale to date-fns's `hi` locale, so "due in 3 days" renders as
  "3 दिन में" rather than mixed-script English. Deliberately *not* exported
  from the i18n barrel — the barrel is in the entry chunk; the date locale
  ships only inside the lazy student chunks that format dates.
- Plurals kept dependency-free with explicit one/many keys (`common.topicsOne`
  / `common.topicsMany`) — Hindi count nouns don't inflect here, English does.
- Server-provided display strings (`priority_display`, `reason_display`)
  intentionally untouched — server-side localization is LA-7 territory.

## Tests

- One renders-in-Hindi case per surface: `AssignmentList.test.tsx` (section +
  CTA + authored-content-stays), `DueForReviewPanel.test.tsx` (title, urgency
  label, practice link), `RecommendationsPanel.test.tsx` (title, score label,
  practice link). Existing rich suites (skeleton/error/empty) untouched and
  green.
- Full suite 54 files / 345 tests green; lint + tsc clean; build + budget
  green (entry 100.45 kB of 160 kB — growth is the English dictionary; Hindi
  stays in its lazy chunk).

## Migration notes

None (frontend only).

## Next steps

LA-4 (AI content language), LA-5 (parity guard + parent/registration/home
chrome — home page added to LA-5 scope per user request).
