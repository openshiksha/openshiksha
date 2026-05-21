# 2026-05-20 — Proficiency Trend Snapshots, Parent Assignment View, Mobile Responsive Pass

## Summary

Three independent features shipped as three atomic PRs, all targeting `modernization`.

---

## Priority 1: Proficiency Trend Snapshots

**PR**: [#80](https://github.com/openshiksha/openshiksha/pull/80)
**Branch**: `feat/2026-05-20-proficiency-trend-snapshots`
**Classification**: New — legacy discarded scores on every proficiency update; no trend tracking existed.

### What was built

- **`StudentProficiencySnapshot` model** (`edge` app): append-only record written by `_recalculate_percentile` after every grading cycle. Never updated — only inserted. Survives even if the live `StudentProficiency` record is deleted or the student moves rooms.
- **Migration**: `edge 0002_add_student_proficiency_snapshot` — one new table, no field changes on existing tables.
- **`GET /api/v1/proficiency/history/?tag=&subject_room=`** action on `StudentProficiencyViewSet`. Students see their own history; parents see a child's history via `?student=<child_id>` (ownership enforced — unlinked students return empty list).
- **`StudentProficiencySnapshotSerializer`** — minimal read-only payload: `{id, score, recorded_at}`.
- **`question_tag` integer FK** added to `StudentProficiencySerializer` — non-breaking addition so the frontend can look up history without a second serializer call.
- **`useProficiencyHistory` hook** (React Query) — fetches snapshot list per (tag, subject_room).
- **`TrendSparkline` SVG component** — pure SVG polyline, no external chart library. Green = improving trend, red = declining, grey = flat. Renders in 80×24px inline.
- **`ProficiencyPage` updated** — sparkline appears next to each proficiency score when ≥2 snapshots exist.

### Tests written

8 new tests in `test_proficiency_history_api.py`:
- Missing params → 400
- Student gets own history
- Empty list when no snapshots yet
- Parent gets child history
- Parent blocked from non-child student history
- Parent without `?student=` gets empty
- `_recalculate_percentile` auto-creates snapshot (integration test)

Full suite: **291 tests passing**, 90% coverage.

### What's different from legacy

Legacy `edge/models.py` had a single `StudentProficiency.score` field overwritten on every recalculation. No history, no trend, no way to answer "am I improving?" This is the first time OpenShiksha has time-series proficiency data.

### Next steps

- Batch `useProficiencyHistory` calls into a single `?tags=1,2,3` endpoint to reduce N+1 parallel requests when the proficiency page has many tags.
- Show child's sparklines on `ParentDashboard` (extends the parent assignment view from Priority 2).
- Feed snapshot history into `PerformancePrediction` AI model for forecasting.

---

## Priority 2: Parent Assignment View

**PR**: [#81](https://github.com/openshiksha/openshiksha/pull/81)
**Branch**: `feat/2026-05-20-parent-assignment-view`
**Classification**: New — legacy parents had zero web visibility into assignments (SMS-only via Pylon).

### What was built

- **`AssignmentViewSet.get_queryset` parent branch**: `GET /api/v1/assignments/?student=<child_id>` returns the child's active assignments, sorted by `-assigned_at`. Ownership enforced — non-linked `?student=` returns empty queryset. `prefetch_related("submissions")` included for the parent branch to avoid N+1 on `child_submission_status`.
- **`child_submission_status` field** on `AssignmentSerializer`: `SerializerMethodField` returning `'submitted'` or `'not_submitted'` for parent role; `None` for all other roles (non-breaking for student/teacher responses). Uses `_prefetched_objects_cache` when present to avoid extra queries.
- **`Assignment` TypeScript interface**: `child_submission_status?: 'submitted' | 'not_submitted' | null` added as optional field.
- **`useChildAssignments` hook** (React Query, 2-minute stale time) — fetches child assignment list with `?student=<child_id>`.
- **`ParentDashboard` tabbed interface**: "Progress" tab (existing proficiency bars) and "Assignments" tab (new). `ChildAssignmentsView` shows assignment cards sorted by due date with colour-coded status badges (green = submitted, amber = pending, overdue label in red).

### Tests written

4 new tests in `test_parent_dashboard_api.py` (10 total):
- Parent sees child assignments via `?student=<child_id>`
- `child_submission_status` is `'not_submitted'` for unsubmitted assignment
- Parent cannot see non-linked child's assignments
- Parent without `?student=` gets empty list

Suite: **287 tests passing**, 89% coverage.

### What's different from legacy

Legacy parents received only SMS notifications via Pylon (`pylon/` app). No web interface existed. Phase 1 (PR #79, May 7) added proficiency bars. Phase 2 (this PR) adds the most practical daily question: "Did my child do their homework?"

---

## Priority 3: Mobile-First Responsive Pass

**PR**: [#82](https://github.com/openshiksha/openshiksha/pull/82)
**Branch**: `feat/2026-05-20-mobile-responsive-student`
**Classification**: New — legacy was desktop-only Django template UI with no mobile consideration.

### What was built

**Navbar** (`features/layout/Navbar.tsx`):
- Hamburger button (`sm:hidden`) with open/close toggle and `aria-expanded`
- Desktop nav links hidden on mobile (`hidden sm:flex`)
- Mobile dropdown: user identity header (name + role badge), role-specific nav links, sign-out button
- `useEffect` closes mobile menu on `location.pathname` change
- `z-20` on nav so dropdown overlays page content

**AssignmentCard** (`features/student/AssignmentCard.tsx`):
- CTA button: `w-full sm:w-auto` (full-width on mobile, auto on desktop)
- Footer: `flex-col sm:flex-row` (stacks vertically on mobile)
- Touch target height: `py-2.5 sm:py-1.5`

**AssignmentDetailPage** (`features/student/AssignmentDetailPage.tsx`):
- Submit button: `w-full sm:w-auto`, `py-3 sm:py-2.5` for 44px+ touch target

**StudentDashboard** (`features/student/StudentDashboard.tsx`):
- Header: `min-w-0` + `truncate` on greeting, `shrink-0` on "My Progress" link

### What's different from legacy

Legacy had no mobile support. India's student demographic skews heavily mobile — students in rural/semi-urban areas may have no desktop. This pass removes the primary UX friction for actual users. Scoped to the three highest-traffic student pages; full site audit remains a lower-priority follow-up.

### Verification

Manual at 375px (Chrome DevTools, iPhone SE preset):
- [ ] Navbar hamburger visible, nav links hidden
- [ ] Tapping hamburger opens mobile menu
- [ ] Nav link tap navigates and closes menu
- [ ] StudentDashboard renders without horizontal scroll
- [ ] AssignmentCard CTA spans full width
- [ ] AssignmentDetailPage submit button spans full width

---

## Migration Notes

Run `python manage.py migrate` to apply `edge 0002_add_student_proficiency_snapshot`. One new table; no changes to existing tables.

## Next Session Priorities

1. Proficiency sparklines on parent dashboard (extends PR #80 + #81)
2. Batch proficiency history endpoint (`?tags=1,2,3`)
3. Question content search (add `subparts__question_text` to `QuestionViewSet.search_fields`)
4. Notification system (email on assignment-due / grading-complete)
