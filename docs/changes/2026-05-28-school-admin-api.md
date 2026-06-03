# School Admin API foundation (P4 backend)

**Date**: 2026-05-28
**Classification**: Improve (legacy handled school structure via Django admin only; this is a real role-guarded, school-scoped product API)
**Branch**: `feat/2026-05-28-school-admin-api`

## Summary

Adds the backend API layer that lets a non-technical school admin run their own
school from a product UI instead of Django admin. A new `IsSchoolAdmin` permission,
a school-scoped `ClassRoomViewSet` (CRUD + soft-delete + enroll/unenroll + summary),
an admin write path on `SubjectRoomViewSet`, and admin-only enrollment-picker
endpoints. No model or migration changes — all models (`School`, `ClassRoom`,
`SubjectRoom`, `User.role`) already existed.

The `/admin` frontend that consumes this API is the natural follow-up.

## Legacy files referenced

- `core/models.py` — `ClassRoom`, `SubjectRoom`, `School` relationships (preserved exactly)
- Legacy school structure (classrooms, enrollment, subject rooms) was managed only
  through Django admin — there was no admin-facing product API and no tenant isolation.

## What changed from legacy and why

| Legacy | Modern |
|--------|--------|
| Django admin only (developer/ops task) | Role-guarded REST API (`IsSchoolAdmin`) |
| Django admin shows all schools to any staff user | Every queryset/write hard-scoped to `request.user.school` |
| Hard delete cascades, orphaning assignments | Soft-delete (`is_active=False`), default list hides inactive |

## Technical details

**Permissions** (`apps/api/views/core.py`):
- `IsSchoolAdmin` — authenticated + `role == ADMIN`.
- `IsTeacherOrSchoolAdmin` — used on `SubjectRoomViewSet` write/enroll actions.

**`ClassRoomViewSet`** (`/api/v1/classrooms/`):
- `get_queryset` filters to `school_id=user.school_id`, annotates `num_students`, hides
  inactive unless `?include_inactive=true`. Admins with no school get an empty queryset.
- `perform_create` forces `school=request.user.school` (ignores any `school` in body),
  catches `IntegrityError` on the `(school, standard, division, academic_year)` unique
  constraint and returns a clean 400.
- `destroy` soft-deletes (`is_active=False`, 204).
- `enroll` / `unenroll` actions — batch, validate-and-report: only same-school student-role
  users are added/removed; unknown/foreign IDs are returned in `invalid_ids` rather than
  failing the whole request.
- `summary` action — classroom/teacher/student/active-subject-room counts for the dashboard.

**`SubjectRoomViewSet`** — extended:
- Admins get `SubjectRoomAdminSerializer` (school-scoped validation of classroom + teacher).
- Write/enroll permissions now `IsTeacherOrSchoolAdmin`.
- `enroll` / `unenroll` actions mirror the classroom ones.
- Duplicate `(classroom, subject)` rejected via the model's `unique_together` → 400.

**`UserViewSet`** — added admin-only `school-teachers` / `school-students` list actions
for enrollment pickers, both force server-side school scoping.

**Serializers** (`apps/api/serializers/core.py`): `ClassRoomSerializer` (read+write, `school`
read-only, `student_count`, class-teacher same-school validation) and
`SubjectRoomAdminSerializer`.

## Tests written

`apps/api/tests/test_school_admin.py` — 17 tests, all passing. Full suite: **503 passed**.

Key cases: non-admin 403 / unauthenticated 401; admin lists only own-school classrooms;
**cross-school admin gets 404 on another school's classroom (the tenancy guard)**; create
forces own school; foreign class-teacher rejected; duplicate classroom 400; soft-delete +
`include_inactive` escape hatch; enroll validate-and-report; admin subject-room create +
foreign-classroom rejection + duplicate rejection + enroll; summary counts; school-scoped
teacher/student picker lists.

## Migration notes

None — no model changes.

## Next steps

- P4 **frontend**: `/admin` route + role guard, classroom list/create, enrollment UI,
  subject-room management, consuming these endpoints.
- Optional: bulk CSV enrollment importer on top of the enroll action.
