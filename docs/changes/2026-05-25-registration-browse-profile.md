# 2026-05-25 — Self-Registration, Open Student Browse, Profile Settings

## Summary

Three features shipped in one PR (#91): student self-registration with classroom join codes (P1), an open-student subject browse interface (P2), and a user profile settings page (P3). Together, these make the platform self-service for the first time — no Django admin needed to onboard any user.

## Classification

- **P1 — Self-Registration + Classroom Join Codes**: New (no equivalent existed — all accounts were admin-created)
- **P2 — Open Student Browse**: New (legacy had Sphinx-driven browse; modern is a simple queryset + React UI)
- **P3 — Profile Settings**: New (no profile page existed in modern frontend)

---

## P1 — Student Self-Registration + Classroom Join Codes

### What Changed From Legacy

Legacy: all user accounts were created by the OpenShiksha team via Django admin. There was no self-service registration flow and no concept of teacher-generated join codes.

Modern: teacher-generated 6-char join codes (Google Classroom–style). Student registers → automatically enrolled in classroom + all active SubjectRooms in one atomic transaction.

### Backend Changes

**New model** `ClassroomInviteCode` (`core/models.py`):
- `ForeignKey` on `ClassRoom` (not `OneToOneField`) — supports deactivating old codes and creating new ones
- `code`: 6-char uppercase alphanumeric, unique, indexed
- `is_active` + `expires_at` for lifecycle management
- `generate_code()` class method: loops until unique (probabilistically safe at school scale)

**New migrations**:
- `0009_add_classroom_invite_code.py`
- `0010_fix_classroom_invite_code_fk.py` — corrected OneToOneField → ForeignKey

**New registration endpoints** (`apps/api/views/auth.py`):
- `POST /api/v1/auth/register/open/` — creates `open_student` account, returns JWT pair
- `POST /api/v1/auth/register/school/` — creates `student` account via join code, auto-enrolls, returns JWT pair
- Both endpoints are unauthenticated (no `IsAuthenticated` permission)
- Password validated via Django's `validate_password`; username case-insensitively unique-checked

**New UserViewSet actions** (`apps/api/views/core.py`):
- `GET /api/v1/users/me/classroom-code/` — lists teacher's active codes
- `POST /api/v1/users/me/classroom-code/` — generates new code for a classroom (deactivates any existing)

**New serializers** (`apps/api/serializers/core.py`):
- `ClassroomInviteCodeSerializer` — read-only, returns `code`, `classroom_id`, `classroom_name`, `is_active`

### Frontend Changes

- `RegisterPage.tsx` — landing with two options (school / independent)
- `RegisterSchoolPage.tsx` — form: name + username + password + email + join code
- `RegisterOpenPage.tsx` — form: name + username + password + email
- `useRegisterMutation.ts` — mutations for both paths, redirect on success (open_student → `/student/browse`, student → `/student`)
- `ClassroomCodeWidget.tsx` — per-classroom code display with Copy + Regenerate buttons
- `TeacherDashboard.tsx` — embeds `ClassroomCodeWidget` per SubjectRoom
- `LoginPage.tsx` — added "Register" link
- `useLoginMutation.ts` — open_student now redirects to `/student/browse`

### Tests Written (17)

| File | Count | Coverage |
|------|-------|----------|
| `test_registration_api.py` | 10 | open registration, school registration, JWT, enrollment, invalid/inactive code, school assignment |
| `test_invite_code.py` | 7 | code generation, teacher CRUD, access control, regenerate deactivates old |

---

## P2 — Open Student Browse Interface

### What Changed From Legacy

Legacy: `sphinx/` had a browse UI coupled to the Cabinet external question store. Modern questions are in the Django DB — browse is a simple annotated queryset, no external service.

### Backend Changes

**New QuestionViewSet action** (`apps/api/views/core.py`):
- `GET /api/v1/questions/browse/` — returns chapters from shared bank (school=None) with question counts
- Filters: `?subject=<id>`, `?standard=<id>`
- Single SQL query: `Chapter.objects.annotate(question_count=Count("questions", filter=Q(...)))`

### Frontend Changes

- `BrowsePage.tsx` — subject dropdown + grade dropdown + chapter list table with question count + Practice link
- `BrowsePracticePage.tsx` — loads up to 10 questions per chapter, renders with existing `QuestionCard`, submit → score summary
- `useBrowseChapters.ts` — React Query hook
- `useStandards.ts` — hardcoded Grade 1–12 (no /standards/ endpoint exists yet)
- `StudentDashboard.tsx` — open student empty-state CTA: "Browse Subjects →"
- `Navbar.tsx` — added "Browse" link for student roles
- `App.tsx` — routes `/student/browse` and `/student/browse/chapter/:chapterId`

---

## P3 — User Profile & Settings Page

### What Changed From Legacy

Legacy: no profile editing existed for students or teachers. Email/phone was set by admins only (`ink.Dossier` was internal CRM — skipped).

### Backend Changes

**New UserViewSet action** (`apps/api/views/core.py`):
- `PATCH /api/v1/users/me/profile/` — allows updating `first_name`, `last_name`, `email`, `phone_number`
- Whitelist enforced: `role`, `school`, `is_staff`, `is_superuser` cannot be changed via this endpoint

**New serializer** (`apps/api/serializers/core.py`):
- `UserProfileUpdateSerializer` — partial=True; validates email format + uniqueness (allows empty)

**UserSerializer** — added `phone_number` to read fields.

### Frontend Changes

- `ProfilePage.tsx` — avatar initials tile + editable form + success toast
- `Navbar.tsx` — user avatar dropdown (initials button) with "Profile" and "Sign out" links, closes on outside click
- `App.tsx` — route `/profile`

### Tests Written (8)

| Test | Description |
|------|-------------|
| `test_student_can_update_own_name` | First + last name updated, persisted |
| `test_student_can_update_own_email` | Email updated, persisted |
| `test_student_cannot_change_own_role` | Role field ignored by update endpoint |
| `test_partial_update_preserves_unchanged_fields` | Partial PATCH leaves untouched fields alone |
| `test_invalid_email_returns_400` | Malformed email → 400 |
| `test_duplicate_email_returns_400` | Email in use by another user → 400 |
| `test_unauthenticated_returns_401` | No token → 401 |
| `test_student_can_update_phone_number` | Phone number updated |

---

## Test Summary

| Suite | Tests | Result |
|-------|-------|--------|
| Full backend suite | 370 | All passed |
| New tests (P1+P3) | 25 | All passed |
| Frontend type-check | — | Pass |
| Frontend lint | — | Pass |
| Frontend build | — | Pass |

## Migration Notes

- `0009_add_classroom_invite_code.py` — new table `classroom_invite_codes`
- `0010_fix_classroom_invite_code_fk.py` — changes field from `OneToOneField` to `ForeignKey` (necessary to support deactivating old codes while creating new ones)
- Both are additive (no column drops)

## Next Steps

| Priority | Feature | Notes |
|----------|---------|-------|
| P0 | LLM Question Generation | Anthropic Claude API integration for teacher question authoring |
| P4 | School Admin Frontend | Admin dashboard for classroom/enrollment management |
| P6 | Lodge Video Content | Video model + chapter-linked video panel |
| P7 | Concierge Enquiry Form | Public contact form for prospective schools |
