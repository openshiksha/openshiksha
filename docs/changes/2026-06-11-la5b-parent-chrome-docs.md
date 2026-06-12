# LA-5b — parent dashboard chrome in Hindi + initiative bookkeeping

**Date:** 2026-06-11
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-5, second half — closes the batch)

## Summary

The parent dashboard (tabs, headings, status badges, empty states, date
labels) renders in Hindi — completing the parent journey: dashboard chrome
(this PR) + AI weekly summary in Hindi (LA-4). Also lands the batch
bookkeeping: initiative ledger rows for LA-1..5, backlog statuses, glossary
growth (~11 terms encountered this batch), STATUS.md headline, and a ROADMAP
refresh that ticks all four stale "Remaining" items (everything previously
listed has shipped).

## Legacy files referenced

None — legacy was English-only.

## What changed and why

- **`ParentDashboard.tsx`** — 21 new `parent.*` keys: page heading, child
  picker (grade chip), overview header, Progress/Assignments tabs, status
  badges (Submitted / Overdue / Pending), proficiency "questions practised"
  counts (one/many), empty states, due/overdue date lines. Dates format with
  `hi-IN` when the locale is Hindi. Authored/server content (subject names,
  chapter tags, problem-set titles) renders as authored (principle 1).
- **Docs:** initiative doc (ledger + backlog ✅s + glossary), STATUS.md
  (headline + active row → next increment LA-6), ROADMAP.md (stale
  "Remaining" items 1–4 ticked with pointers to the initiatives that closed
  them; board now points to the initiatives STATUS as the live tracker).

## Tests

- New `ParentDashboard.test.tsx` (English chrome + full-Hindi chrome with
  authored-content-stays assertion).
- Full suite 57 files / 355 tests green; lint/tsc/build/budget green
  (entry 104.68 kB of 160 kB).

## Migration notes

None (frontend + docs only).

## Next steps

LA-6 (teacher chrome) is the natural next batch anchor; LA-7 (localized
emails via `preferred_language`); LA-8 (`Intl` numbers/dates).
