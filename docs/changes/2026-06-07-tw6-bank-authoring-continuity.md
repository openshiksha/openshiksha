# TW-6 — Question-bank ↔ authoring continuity

**Classification:** Improve (frontend-only).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw6-bank-authoring-continuity`.

## Summary

Closes the last "context loss" seam in the teacher workspace: filter state on
`QuestionBankPage` now lives in the URL, so back-button after a detour
through the editor or set builder restores the exact same search. New
"Use in new set" action seeds a freshly-built problem set with the focused
question. Both Edit and Use-in-new-set carry a `returnTo` query param so the
destination page can offer "Back to question bank" that lands on the same
filtered view.

## Why

The bank already had healthy reuse paths (preview, add-to-existing-set via
side sheet) but the moment a teacher jumped out — to fix a typo, or build a
new set around a question — they lost everything. `useState` for filters and
`navigate('/teacher/questions')` for "back" both erased context. URL-state +
`returnTo` makes the round-trip free.

## Changes

- `frontend_modern/src/features/teacher/QuestionBankPage.tsx`
  - Filters (`q`, `subject`, `chapter`, `diff`, `focus`) read/write via
    `useSearchParams`; `useDeferredValue(search)` replaces the manual debounce.
  - Edit button (row + preview footer) and new **Use in new set** button
    encode the current URL as `returnTo=…`.
- `frontend_modern/src/features/teacher/CreateProblemSetPage.tsx`
  - Reads `?seedQuestion=<id>` → fetches via `useQuestion`, pre-fills subject /
    chapter / selection on first load.
  - Reads `?returnTo=…` → success state swaps "Back to dashboard" for
    "Back to question bank" when returning makes sense.
- `frontend_modern/src/features/teacher/CreateQuestionPage.tsx`
  - Reads `?returnTo=…` (defaults to `/teacher/questions`) so the Back link
    and post-save "Back to question bank" button respect the originating
    search.
- `frontend_modern/src/features/teacher/QuestionBankPage.test.tsx` — new,
  5 tests covering URL hydration, filter push, clear, Use-in-new-set
  navigation, and Edit returnTo.

## Verify

- `npm run lint`, `npm run type-check` clean.
- `npx vitest run …QuestionBankPage.test.tsx` — 5/5. Full suite 226/226.
- `npm run build` + `npm run check:budget` — entry 93.09 kB / 160 kB budget.

## Next

TW-7 (mobile teacher pass) — the last unblocked initiative item.
