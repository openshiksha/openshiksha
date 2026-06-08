# TW-7 — Mobile teacher pass

**Classification:** Improve (frontend-only).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw7-mobile-teacher`.

## Summary

The two long teacher authoring forms — `CreateAssignmentPage` and
`CreateProblemSetPage` — buried their primary CTA at the bottom of a multi-card
form. On a phone that meant scrolling past the whole preview / picker to hit
"Publish" or "Create". This change adds a `lg:hidden` sticky bottom action bar
on both pages that keeps the primary action one tap away on mobile, while
desktop keeps its inline button (no duplication on big screens). Date-preset
chips on the assignment form bump up to a 44 px touch target on mobile.

## Why

Initiative principle #6 ("no dead-ends"): on a phone the existing form was a
de-facto dead-end if you couldn't scroll patiently to the submit button. The
mobile bar surfaces the action without changing desktop behaviour.

## Changes

- `frontend_modern/src/features/teacher/CreateAssignmentPage.tsx`
  - Add a `lg:hidden` fixed bottom bar containing a full-width submit button
    that triggers the existing form `onSubmit`.
  - Bump page bottom padding (`pb-28 lg:pb-8`) so the last form card doesn't
    sit under the bar.
  - Date-preset chips: `px-4 py-2 text-sm sm:px-3 sm:py-1 sm:text-xs` so the
    touch target hits ~44 px on mobile and stays compact on desktop.
- `frontend_modern/src/features/teacher/CreateProblemSetPage.tsx`
  - Hide the inline submit on mobile (`hidden … lg:flex`); add a `lg:hidden`
    sticky Create bar with the same disabled-state hints and a selected-count
    pill on the button itself (`Create (3)`).
  - Same bottom-padding bump.
- `frontend_modern/src/features/teacher/CreateAssignmentPage.test.tsx` — new
  test: mobile bar exists, is `lg:hidden`, holds a `type="submit"` button.
- `frontend_modern/src/features/teacher/CreateProblemSetPage.test.tsx` — new,
  one test for the mobile bar's presence + disabled hint copy.

## Verify

- `npm run lint`, `npm run type-check` clean.
- Vitest 223/223. New tests pass.
- `npm run build` + `npm run check:budget` — entry 93.05 kB / 160 kB.
- Manual: resize to ≤ 1024 px width → bar appears; ≥ 1024 px → desktop layout.

## Next

This closes the last unblocked Teacher Workspace increment. TW-2 (editable
preview) is still blocked on Authoring Integrity Phase 1.
