# TW-4 — Dashboard "needs attention" strip

**Classification:** Improve (frontend-only).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw4-needs-attention`.

## Summary

Add a top-of-page `NeedsAttentionPanel` above the room cards on
`TeacherDashboard`. It derives three buckets from `useTeacherAssignments`
data the dashboard already loads — **overdue** (past-due, not all submitted),
**ungraded** (past-due, fully submitted, no grades yet), **low completion**
(past-due, graded, < 50% submitted) — with explicit precedence
(`overdue > ungraded > low completion`) so each assignment lands in at most one
bucket. Chips deep-link to the earliest-due item in the bucket.

The strip is hidden entirely when nothing needs attention (no dead weight per
initiative principle #5).

## Why

The dashboard surfaced everything at one altitude — a busy teacher had no
"what needs me first" signal. PERF-decluttered analytics live behind the
"View class insights" disclosure; this elevates the small set of items that
genuinely need a teacher up top.

## Changes

- `frontend_modern/src/features/teacher/needsAttention.ts` — pure
  `bucketize()` helper (split out so component file stays component-only and
  passes `react-refresh/only-export-components`).
- `frontend_modern/src/features/teacher/NeedsAttentionPanel.tsx` — the strip.
- `frontend_modern/src/features/teacher/TeacherDashboard.tsx` — render strip
  above the headline stats.
- `frontend_modern/src/features/teacher/NeedsAttentionPanel.test.tsx` —
  9 tests covering bucketize precedence, no-double-counting, hidden-when-empty,
  and earliest-due deep-link.

## Verify

- `npm run lint` clean. `npx vitest run …NeedsAttentionPanel.test.tsx` — 9/9.
- `npm run build` + `npm run check:budget` — entry 92.99 kB / 160 kB budget.

## Next

TW-3a/b (assignment close/reopen + due-date edit) and TW-T (e2e) follow.
