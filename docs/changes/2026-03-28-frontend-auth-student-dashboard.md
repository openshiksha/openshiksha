# Frontend Auth + Student Dashboard + /api/users/me/

**Date**: 2026-03-28
**Branch**: fix/test-problemset-name-field (merged into modernization via PR #58)
**Classification**: New (frontend) + Port/Improve (backend API) + Fix (CI tests)

## Summary

First real frontend pages for OpenShiksha. Before this PR, the entire frontend was placeholder `<div>` strings. After this PR:
- Students can open the browser, see a login form, sign in with JWT credentials, and be routed to their assignment dashboard
- The dashboard shows all assignments grouped by status (Overdue, Due Soon, Upcoming, Completed) with progress and scores
- Shared layout shell exists for all future authenticated pages to build on

Also included:
- `GET /api/users/me/` backend endpoint (needed for role-based routing after login)
- CI test fixture fixes that unblocked the test suite

## Legacy Reference

The original OpenShiksha used Django templates (Bootstrap 3) — entirely server-rendered, desktop-only, no React. The modern frontend is entirely new design territory. Concepts borrowed from legacy:
- Assignment grouping by due status (legacy had "today/upcoming/overdue" sections)
- Progress indicators per assignment (legacy used colored progress bars)
- Role-based routing (teacher vs student home pages)

## What's New vs Legacy

| Aspect | Legacy | Modern |
|--------|--------|--------|
| Frontend framework | Django templates | React 18 + TypeScript |
| Auth | Django sessions (CSRF cookie) | JWT (access + refresh tokens) |
| Assignment grouping | Server-rendered Django view | React Query + client-side grouping |
| Loading states | Page reload | Async spinners, React Query |
| Mobile | Desktop-only | Mobile-first (Tailwind responsive) |

## Technical Details

### Backend: `/api/users/me/`
- Added `UserViewSet(GenericViewSet)` with a single `@action(detail=False, methods=['get'], url_path='me')` 
- Returns `{ id, username, email, first_name, last_name, role }` for the authenticated user
- Used after login to determine routing: teacher → /teacher, student → /student

### Frontend Architecture
```
src/
  features/
    auth/
      LoginPage.tsx          — Centered card form, loading state, inline errors
      useLoginMutation.ts    — React Query mutation: login → store tokens → fetch user → navigate
    layout/
      AppShell.tsx           — Navbar + main content wrapper
      Navbar.tsx             — Brand, nav links, role badge, logout button
      ProtectedRoute.tsx     — Auth guard: redirect to /login if unauthenticated
    student/
      StudentDashboard.tsx   — Greeting + assignment list
      AssignmentList.tsx     — Groups assignments into 4 buckets using date-fns
      AssignmentCard.tsx     — Subject/chapter/due date/progress bar/score/CTA
      useAssignments.ts      — React Query: GET /api/assignments/ with 30s stale time
  shared/
    components/
      LoadingSpinner.tsx     — Reusable animated spinner
    hooks/
      useAuth.ts             — Expanded: verifyToken + getCurrentUser + logout
  types/index.ts             — Full Assignment, Submission, ProblemSet, SubjectRoom, User types
```

### Assignment Grouping Logic
```typescript
overdue:   !submitted && isPast(due_at)
dueSoon:   !submitted && !isPast(due_at) && differenceInDays(due_at, now) <= 3
upcoming:  !submitted && !isPast(due_at) && differenceInDays(due_at, now) > 3
completed: !!submitted_at
```

### Token Storage
- `localStorage` for MVP (noted with TODO for httpOnly cookie upgrade)
- Auto-refresh on 401 already in `api/client.ts` interceptor

## CI Test Fixes (also included)

Two test fixture bugs unblocked by the same PR:
1. `ProblemSet` uses `title=` (not `name=`) and requires `chapter=`
2. `Assignment` uses `assigned_by=` (not `created_by=`) and requires `due_at=`
3. Cascade test must delete `Submission` before `User` (Submission.student is `PROTECT`)

## Tests Written

- `src/features/auth/LoginPage.test.tsx`:
  - Renders username and password fields
  - Submit button disabled when fields empty, enabled when filled
  - Shows error alert on failed login
  
- `src/features/student/AssignmentList.test.tsx`:
  - Empty state shown when no assignments
  - Correct grouping into Upcoming / Due Soon / Overdue / Completed sections
  - Multiple assignments categorized separately

## Migration Notes

No database migrations required — all changes are frontend or existing model endpoints.

## Next Steps

1. **Assignment detail page** — View questions, enter answers, submit. Needs KaTeX math rendering (`katex` already in package.json). This is the core student interaction.
2. **Teacher dashboard** — SubjectRoom list, create assignment. Teachers are gatekeepers.
3. **Cabinet integration** — Wire `CabinetClient` to serve question content (currently questions have `correct_answer` but no text).
4. **Parent dashboard** — Read-only proficiency view for their child.
