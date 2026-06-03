# Teacher Question Bank, SRS Due Panel, Parent Dashboard

**Date**: 2026-05-07
**PR**: [#79](https://github.com/openshiksha/openshiksha/pull/79)
**Branch**: `feat/2026-05-07-teacher-question-bank`
**Classification**: New (all three priorities)

---

## Summary

Three high-priority UX gaps closed in one session:

1. **Teacher Question Bank** — teachers can now browse the full question corpus via `/teacher/questions`
2. **Student SRS Panel** — the SM-2 spaced repetition engine is now visible to students
3. **Parent Dashboard** — the `parent` role has its first functional UI

---

## Priority 1: Teacher Question Bank

### What was missing
Teachers could create questions but had no way to browse them without Django admin. Every assignment workflow required remembering question IDs.

### What was built
- **Backend** — `QuestionSerializer` extended with `chapter_name`, `subject_name`, `standard_number`, `question_type_display` (DRF source fields, no migration)
- **Frontend** — `useQuestionList.ts` extended with `search` and `difficulty` filter params
- **Frontend** — `QuestionBankPage.tsx` — searchable/filterable card grid
  - Type badges (MCQ=indigo, numeric=green, fill_blank=amber, multi_select=purple, matching=pink)
  - Difficulty dots (1–5 filled/empty circles)
  - Subject + Chapter name per card
  - First subpart question_text preview (120 char, raw — no KaTeX render in list)
  - Tag chips (up to 3, then "+N more")
  - Debounced search (300ms, useRef — no window globals)
  - Empty state with CTA to create question
- **Frontend** — `/teacher/questions` route in `App.tsx`
- **Frontend** — "Questions" Navbar link for teachers; teacher Dashboard active check narrowed to `=== '/teacher'`
- **Types** — `Question` interface: `standard_number?`, `subject_name?`, `chapter_name?`, `question_type_display?`; `User` interface: `grade?`

### Legacy comparison
Legacy used an external Cabinet service (Sphinx UI). Questions browsable only with Cabinet online. Modern: all in PostgreSQL, instant search, no external dependency.

### Known limitation
`search_fields = ["chapter__name", "subject__name"]` — searches chapter/subject names, not question content. Searching "quadratic" by question text won't work. Future: add `subparts__question_text` to `search_fields`.

---

## Priority 2: Student SRS "Due for Review" Panel

### What was missing
`SpacedRepetitionEntry` records with `next_review_date` existed in the DB and `/api/ai/spaced-repetition/due/` was live — but students had no visibility whatsoever.

### What was built
- **Frontend** — `useSpacedRepetitionDue.ts` hook — queries `/api/ai/spaced-repetition/due/`, handles plain array or paginated response (10-min staleTime)
- **Frontend** — `DueForReviewPanel.tsx`
  - Urgency levels: overdue (red dot), today (amber dot), soon (blue dot)
  - Sorted by `next_review_date` ascending (most urgent first)
  - Capped at 5 entries + "+N more" note
  - Self-hides when no due entries (no conditional wrapper needed at call site)
  - Shows interval + repetition count per entry
- **Frontend** — Added to `StudentDashboard.tsx` after `RecommendationsPanel`

### Legacy comparison
No spaced repetition existed in legacy. This is a net new feature.

---

## Priority 3: Parent Dashboard

### What was missing
`UserRole.PARENT` existed in models and the JWT auth system, but parents who logged in hit a `/student` redirect. The role was a dead end.

### What was built

**Backend:**
- `IsParent` permission class
- `IsStudentOrParent` composite permission (prevents teachers from accessing proficiency endpoint, which was a regression from the parent-aware refactor)
- `UserViewSet.children` — `GET /api/v1/users/me/children/` (parent-only via `IsParent`)
- `StudentProficiencyViewSet` — refactored `get_queryset()`:
  - Students: see their own records (unchanged behavior)
  - Parents: see a child's records via `?student=<child_id>`; ownership enforced via `user.children.filter(id=child_pk).exists()`; integer validation prevents ValueError on non-integer params
  - Teachers/others: still 403 (via `IsStudentOrParent` permission class)
- `UserSerializer` — `grade` field added (was on the `User` model but missing from the serializer)
- 6 new tests in `test_parent_dashboard_api.py`

**Frontend:**
- `features/parent/useChildren.ts` — fetches `GET /api/v1/users/me/children/`
- `features/parent/useChildProficiency.ts` — fetches `/api/v1/proficiency/?student=<childId>`
- `features/parent/ParentDashboard.tsx`
  - Child tab selector (button tabs for multi-child families; single child shows directly)
  - `ChildView` — proficiency bars grouped by subject, color-coded (green ≥70%, yellow ≥40%, red <40%)
  - Loading + empty states per child
  - Grade display when available
- `/parent` route in `App.tsx`
- `defaultPath` updated: parent role redirects to `/parent`
- Parent Navbar link

### Security
- `user.children.filter(id=child_pk).exists()` — parent can only access their own children's data
- Integer parsing guards against `?student=abc` type attacks
- `IsStudentOrParent` permission ensures teachers never accidentally gain access

### Legacy comparison
No parent portal existed in legacy. Parents received SMS notifications (Pylon) but had no web-based progress view. This is a net new experience.

---

## Tests

| Suite | Count | Result |
|-------|-------|--------|
| New: `test_parent_dashboard_api.py` | 6 | ✅ All pass |
| Full backend suite | 283 | ✅ All pass |
| Frontend type-check | — | ✅ 0 errors |
| Frontend lint | — | ✅ 0 warnings |
| Frontend build | — | ✅ Clean |

---

## Files Changed

**Backend:**
- `backend/openshiksha/apps/api/serializers/core.py` — QuestionSerializer name fields, UserSerializer grade
- `backend/openshiksha/apps/api/views/core.py` — IsParent, IsStudentOrParent, UserViewSet.children, StudentProficiencyViewSet parent support
- `backend/openshiksha/apps/api/tests/test_parent_dashboard_api.py` — new

**Frontend:**
- `frontend_modern/src/types/index.ts` — Question name fields, User.grade
- `frontend_modern/src/App.tsx` — QuestionBankPage + ParentDashboard routes, parent redirect
- `frontend_modern/src/features/layout/Navbar.tsx` — Questions link, parent link, isParent flag
- `frontend_modern/src/features/teacher/useQuestionList.ts` — search + difficulty filters
- `frontend_modern/src/features/teacher/QuestionBankPage.tsx` — new
- `frontend_modern/src/features/student/useSpacedRepetitionDue.ts` — new
- `frontend_modern/src/features/student/DueForReviewPanel.tsx` — new
- `frontend_modern/src/features/student/StudentDashboard.tsx` — DueForReviewPanel added
- `frontend_modern/src/features/parent/useChildren.ts` — new
- `frontend_modern/src/features/parent/useChildProficiency.ts` — new
- `frontend_modern/src/features/parent/ParentDashboard.tsx` — new

---

## Next Steps

- **Teacher question bank**: add `search_fields = ["subparts__question_text"]` to enable content search
- **SRS drill UI**: let students practice specifically from their SRS backlog (requires new assignment flow)
- **Parent dashboard**: add assignment completion status (submitted/pending/overdue) per child
- **Proficiency trends**: StudentProficiency history model for score-over-time charts
