# School Admin frontend (P4 frontend)

**Date**: 2026-05-28
**Classification**: Improve (legacy school structure was managed only via Django admin; this is a role-guarded admin product UI)
**Branch**: `feat/2026-05-28-school-admin-frontend` (based on `modernization`)

## Summary

The `/admin` product surface that consumes the P4 backend School Admin API. A
school admin can now run their school from the UI instead of Django admin:
view a school summary, create/archive classrooms, manage classroom rosters,
and create subject rooms (assign a teacher + enroll students) — all hard-scoped
to their own school by the backend.

This is the frontend half of P4; the backend (`IsSchoolAdmin`, `ClassRoomViewSet`,
admin `SubjectRoomViewSet` write path, enrollment-picker endpoints) ships separately
on `feat/2026-05-28-school-admin-api`.

## What was added

**Routing & guard**
- `ProtectedRoute` gained an optional `allowedRoles` prop — users without the role
  are redirected to their default landing (`/`).
- New routes `/admin` and `/admin/classrooms/:id`, both guarded to `UserRole.ADMIN`.
- `App.tsx` default landing for `admin` role is now `/admin` (previously fell through
  to `/student`).
- Navbar shows a "School Admin" link (desktop + mobile) for admins.

**Feature (`src/features/admin/`)**
- `useAdminSummary` — `GET /classrooms/summary/` (dashboard counts).
- `useClassrooms` — list (with `?include_inactive`), retrieve, create, update,
  soft-delete (archive), and enroll/unenroll mutations.
- `useSchoolPeople` — `GET /users/school-teachers/` and `/users/school-students/`
  for the teacher-assignment and enrollment pickers.
- `useAdminSubjectRooms` — list (admin sees own-school rooms), create, enroll/unenroll.
- `AdminDashboard` — summary cards, classroom list, inline "New Classroom" form,
  "Show archived" toggle, archive action.
- `ClassroomManagePage` — classroom roster management + subject-room list/create/
  enrollment for a single classroom.
- `EnrollStudentsModal` — reusable searchable student picker used for both classroom
  and subject-room enroll/unenroll; surfaces the API's validate-and-report
  `invalid_ids` ("N skipped").

## Tests

`EnrollStudentsModal.test.tsx` — 5 tests (render, search filter, disabled-until-selected,
onAction payload, invalid-id reporting). Full FE suite: **16 passed**. `tsc --noEmit`
and production `vite build` both clean; lint clean.

## Known limitations / follow-ups

- The backend `ClassRoomSerializer` exposes `student_count` but not the enrolled
  student list, so the roster UI works from the full school-students list (enroll/
  remove by selection) rather than showing current members. Exposing a roster field
  is a natural backend follow-up for a richer UI.
- Standard options reuse the existing synthetic `useStandards` (1–12), consistent with
  the teacher authoring UI; there is no `/standards/` endpoint yet.
- Not browser-verified against a live API in this session — the P4 backend lives on a
  separate unmerged branch. Type-check, build, and unit tests pass against the known
  API contract.

## Next steps

- Merge order: P4 backend PR first, then this FE PR (FE calls those endpoints).
- Optional: bulk CSV enrollment importer on top of the enroll action.
