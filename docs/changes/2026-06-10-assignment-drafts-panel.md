# AssignmentDraftsPanel — first consumer of /ai/assignment-drafts/ (ASA-6)

**Date:** 2026-06-10
**Classification:** New (batch anchor)
**Initiative:** AI Surface Activation — ASA-6 (daily plan 2026-06-10 PR 5)

## Summary

`/ai/assignment-drafts/` was a fully built, fully tested teacher feature —
generate → review rationale → approve into a real ProblemSet + Assignment —
with zero frontend consumers. This PR wires it: a collapsible "AI Assignment
Drafts" panel inside each subject-room's insights on the teacher dashboard.
One click takes a teacher from "my class is weak on X" to a reviewable draft,
and one more to a live assignment. 3 of the 4 dark `/ai/` endpoint groups are
now lit; only ASA-7 (open-response grading) remains.

## Legacy reference

Legacy assignment creation (`core/`, `sphinx/`) had teachers pick an existing
ProblemSet and a due date — no help choosing *what* to assign; the insight
about which chapters are weak lived in a separate analytics page. ASA-6 fuses
insight and action: the draft *is* the analytics conclusion, with rationale a
teacher can read and overrule. Kept: teacher final say (approve/dismiss,
title/due-date control). Improved: AI-targeted selection with provider
transparency.

## What changed

- **`frontend_modern/src/features/teacher/useAssignmentDrafts.ts`** (new) —
  `AssignmentDraft` type mirroring `AssignmentDraftSerializer`;
  `useAssignmentDrafts(subjectRoomId, enabled)` list query (handles both
  array and `{results}` shapes) with `refetchInterval` polling **only while a
  draft is pending** (3 s, stops by itself); `useGenerateAssignmentDraft`,
  `useApproveAssignmentDraft`, `useDismissAssignmentDraft` mutations, each
  invalidating the room's list; `errorDetail()` helper for axios-shaped 409s.
- **`frontend_modern/src/features/teacher/AssignmentDraftsPanel.tsx`** (new) —
  structural copy of the sibling insight panels (collapsed by default, fetch
  on expand, per-room):
  - **pending** card: pulsing "Assembling a draft from your class's weak
    spots…" (polling flips it to ready/failed).
  - **ready** card: title, rationale, target-chapter chips with class
    averages, question count + estimated minutes, `✨ AI-generated` vs
    `Auto-drafted` + stub note from `model_used`; **Approve…** opens an
    inline form (due date, default 7 days out, ISO on submit like
    `CreateAssignmentPage`; optional title override); **Dismiss**.
  - **approved** card: "Assigned" badge + react-router `Link` to
    `/teacher/assignments/{approved_assignment}`.
  - **failed** card: friendly line + `error_detail` + "Try again"
    (re-generates with the same size/difficulty).
  - 409 on approve surfaces the server's `detail` (e.g. no active questions →
    regenerate hint).
  - List-error → "Couldn't load drafts" + Retry (never the empty state, per
    this batch's sweep); loading → 2 shape-matched skeletons; empty → an
    explanatory card.
  - Generate controls: question count (1–20, default 8) + difficulty (1–5,
    default 2) + "Draft an assignment". Footer: "AI proposes, you decide."
- **`frontend_modern/src/features/teacher/TeacherDashboard.tsx`** — panel
  mounted in `RoomInsights` alongside `InterventionsPanel` /
  `MisconceptionClustersPanel`. Mounting per subject-room (prop, not a room
  select) matches how the sibling panels already work — the plan's SubjectRoom
  dropdown became unnecessary.

## Backend

None — `AssignmentDraftViewSet` (views.py:1450) was already complete,
permission-scoped (teacher's own rooms only) and tested; no serializer gaps
surfaced.

## Tests

`AssignmentDraftsPanel.test.tsx` — 10 cases: collapsed-by-default +
skeleton-not-empty while loading; explanatory empty state; ready-card render
(rationale, chips, counts, provenance badge, actions); stub Auto-drafted
path; generate → pending card; approve happy path (asserts the assignment
link); approve 409 surfaces server detail; dismiss removes the card; failed
card with error detail + retry; list-error + Retry recovery.

Full gate: lint, `tsc --noEmit`, `vitest run` (290 passed / 48 files),
`npm run build` — all green.

## Next steps

- ASA-7 (open-response grading UI) — last dark endpoint group, its own
  batch-anchor run.
- Continuous-improvement pool: shared `AIBadge`, `useAsyncGeneration` hook
  (this panel re-implements the 202-then-poll pattern a third time).
- Manual Docker-stack screenshot pending (stack not running in this session);
  panel follows the proven sibling-panel layout.
