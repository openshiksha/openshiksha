# Legacy Feature-Parity Audit (M7-04)

> Source-of-truth audit of every legacy Django 1.11 app against its modern
> Django 4.2 + React equivalent. Open this when scoping a port, when triaging
> "does the modern app do X?", or when planning to retire a legacy app.
>
> Generated: 2026-06-04. Owner of edits: any contributor finishing a port —
> tick the row and link the PR.

## Legend

- ✅ **Ported** — full behaviour lives in the modern stack.
- 🟡 **Partial** — covered partially; missing slice noted in the row.
- ⛔ **Skipped** — intentionally not ported (reason in the row).
- ⏳ **TODO** — not yet ported, on the modern backlog.

## At-a-glance

| Legacy app | Status | Modern home | Notes |
|---|:--:|---|---|
| `core/` | ✅ | `backend/openshiksha/apps/core/` | Board/School/Standard/Subject/Chapter/ClassRoom/SubjectRoom/Question/QuestionSubpart/Assignment/Submission all ported. GenericFK → direct FK; `UserInfo`/`SchoolProfile` merged into `User`/`School`. |
| `edge/` | ✅ | `backend/openshiksha/apps/edge/` | Tick + StudentProficiency + SubjectRoomProficiency + SubjectRoomQuestionMistake all ported, plus modern additions (percentile snapshots, regression field, `StudentProficiencySnapshot` time-series). |
| `grader/` | ✅ | `backend/openshiksha/apps/core/tasks.py::grade_submission` | Per-submission real-time grading replaces nightly batch. |
| `focus/` | ✅ | `ProblemSet.is_remedial` + `_create_remedial_assignment()` + `target_student` FK | Per-student remedials of *only* the wrong questions (PR #84/#87). |
| `croupier/` | ✅ | `backend/openshiksha/apps/api/croupier.py` | Deterministic per-(student_id, subpart_id) seeded MCQ shuffle + variable substitution. M7-02 (#140) wired this into the student list endpoint. |
| `sphinx/` | ✅ | `frontend_modern/src/features/teacher/CreateQuestionPage.tsx` | Authoring with KaTeX preview, variable-constraints panel, AI-generation panel (Gemini JSON mode, #185). Migrated to V2 in M4-07c / #192. |
| `cabinet/` | ✅ | DB-stored `Question`/`QuestionSubpart` + import command | Cabinet imports baked in; **Cabinet Data Fidelity** initiative is closed (audit `--strict` green on 646 questions). External cabinet service retired. |
| `pylon/` (SMS) | 🟡 | `backend/openshiksha/apps/core/emails.py` | **Replaced** with email (no SMS in modern). Phase 1 (grading complete + remedial assigned) shipped; due-date reminder still TODO. Legacy SMS-to-Indian-providers integration intentionally not ported. |
| `concierge/` | ✅ | `backend/openshiksha/apps/concierge/` + `frontend_modern/src/features/enquiry/EnquirePage.tsx` | `Enquirer` model + public POST + `notify_enquiry_received` (mail_admins) + V2 page (M3-03 #199). **Activation gap:** `ADMINS` is not set in `settings/`, so the email currently no-ops. See the "Known gaps" section. |
| `lodge/` | ✅ | `backend/openshiksha/apps/lodge/` + `frontend_modern/src/features/student/VideosPanel.tsx` | `Video` model + `GET /api/videos/?chapter=<id>`; `VideosPanel` renders per-chapter videos on Assignment detail. M4-06b-ii (#189) reskinned to V2. |
| `ink/` (Dossier) | 🟡 | `User.phone_number`, `User.email` (`shared/ProfilePage.tsx`) | Primary email + phone ported. **`secondaryPhone` / `secondaryEmail` / `flagged`** intentionally skipped — legacy CRM-only fields, not user-facing product. |
| `challenge/` | ⛔ | n/a | A memorisation-game / honeypot view rendering a 1000-element RANDOM_DATA list. No identified product value; deliberately not ported. |
| `frontend/` (Django templates) | ⛔ | n/a — replaced wholesale | The legacy Django-template UI was superseded by `frontend_modern/` React app. |

## Capabilities — by audience

### Student

| Capability | Legacy | Modern | Status |
|---|---|---|---|
| Practice + auto-grade an assignment | `core` + `grader` | `AssignmentDetailPage` + `grade_submission` Celery task | ✅ |
| Per-student MCQ shuffle + variable substitution | `croupier` | `QuestionWithSubpartsStudentSerializer` | ✅ (M7-02 / #140) |
| Self-directed Browse by board → subject → chapter | new in modern | `BrowsePage` + `BrowsePracticePage` | ✅ V2 (#188) — Grade filter parity fixed (M7-03 #194 / #197) |
| Per-chapter mastery / proficiency view | `edge.StudentProficiency` | `ProficiencyPage` (sparklines from `StudentProficiencySnapshot`) | ✅ V2 (M4-06a #183) |
| Targeted remedial assignments | `focus` | `ProblemSet.is_remedial` + auto-assigned per-student | ✅ |
| Streaks + grace day + milestone tiers | none in legacy | `StudentStreak` + `StreakBadge` | ✅ (modern addition) |
| Spaced repetition drill | none in legacy | `apps/ai/` SM-2 engine + `/student/srs/drill` | ✅ (modern addition; M4-05 V2 #185) |
| Chapter videos | `lodge.Video` | `VideosPanel` (per-chapter, conditional render) | ✅ V2 (M4-06b-ii #189) |
| Question images | `cabinet` base64 | `QuestionSubpart.image_url` URLField | ✅ (#86) |
| Hints + worked solutions | `cabinet` `solution`, `hint` fields | `QuestionSubpart.solution_text` + `hint_text` | ✅ |
| Profile / settings | `ink.Dossier` | `ProfilePage` + `PATCH /users/me/profile/` | ✅ V2 (M4-08 #180); password change still TODO |
| Mobile primary navigation | n/a (legacy was desktop-only) | `BottomNav` (Home/Browse/Path/Profile) | ✅ (M5-01 #195) |
| AI tutor / Socratic chat | none in legacy | branch `ai/2026-06-04-ai-tutor-chat` (in flight) | 🟡 (separate track) |

### Teacher

| Capability | Legacy | Modern | Status |
|---|---|---|---|
| Author questions (LaTeX preview + variables) | `sphinx` | `CreateQuestionPage` + `RichContent` | ✅ V2 (#192) |
| Edit existing question | server-rendered form | `/teacher/questions/:id/edit` (reuses `CreateQuestionPage` in edit mode) | ✅ |
| AI-assisted question generation | none | Gemini JSON-mode panel in `CreateQuestionPage` | ✅ (#185, hardened V2 #192) |
| Question bank (browse / search / filter) | `cabinet` browse views | `QuestionBankPage` + `useQuestionList` | ✅ V2; search dedup + standard-number filter fixed (M7-03 #197) |
| Compose problem sets | `core` admin | `CreateProblemSetPage` (preview-driven) | ✅ V2 |
| Compose assignments | `core` | `CreateAssignmentPage` | ✅ V2 |
| Class health + weekly summary | mostly server reports | `ClassHealthPanel` + `WeeklyReportPanel` (AI-summarised) | ✅ V2 (M4-07a #190) |
| Per-assignment submission/score breakdown | `core` admin | `TeacherAssignmentDetailPage` | ✅ V2 (M4-07b #191) |
| Classroom join code | none in legacy | `ClassroomInviteCode` + `ClassroomCodeWidget` | ✅ V2 (M4-07a #190) |

### Parent

| Capability | Legacy | Modern | Status |
|---|---|---|---|
| Parent–child link | `core.Home` | `User.children` M2M | ✅ |
| Child proficiency trend + assignment view | none in legacy | Parent dashboard with sparklines + activity panels | ✅ V2 (M4-02 #181) |

### Admin (school)

| Capability | Legacy | Modern | Status |
|---|---|---|---|
| Manage classrooms (list, create, edit) | `core` admin via Django | `AdminDashboard` + `ClassroomManagePage` | ✅ V2 (M4-04 #182) |
| Manage students per classroom | Django admin | UI in `ClassroomManagePage` (enroll / remove) | ✅ V2 |
| Manage SubjectRooms (assign teachers) | Django admin | covered via `ClassroomManagePage` | ✅ V2 |
| `school-teachers` list (enrollment picker) | Django admin | `GET /users/school-teachers/` | ✅ |

### Public / marketing

| Capability | Legacy | Modern | Status |
|---|---|---|---|
| Marketing home (Practice / Evaluate / Analyse) | legacy `frontend/` Django templates | `HomePage` (V2 chalkboard hero + sections) | ✅ |
| Login (branded) | legacy template | V2 chalkboard/paper `LoginPage` | ✅ |
| Register (Open / School / Open student) | partial in legacy | three V2 register pages composing `AuthLayout` | ✅ |
| Enquire (prospective schools) | `concierge` template | V2 `EnquirePage` composing `AuthLayout` | ✅ V2 (M3-03 #199) |

## Known gaps (TODO)

1. **`concierge` enquiry email delivery.** `notify_enquiry_received` calls
   `mail_admins(...)` correctly, but `ADMINS` isn't set in any `settings/`
   module — so the email no-ops in both dev and prod. Enquiries are still
   captured in the DB (visible at `/admin/concierge/enquirer/`). Fix: load
   `ADMINS` from `OPENSHIKSHA_ADMIN_EMAILS` env var in `settings/production.py`.
   *Small follow-up; ~5 lines.*

2. **Due-date email reminder** (legacy `pylon` had SMS equivalent). The Phase 2
   note in `CLAUDE.md` flags this — Celery beat schedule already exists for
   `send_due_date_reminders`, but the email template + per-student opt-out
   are TODO.

3. **Password change** on the Profile page. Backend endpoint pending; UI
   placeholder noted in `M4-08`.

4. **Question file upload** (replace URL pasting with a real upload). The
   `QuestionSubpart.image_url` URLField was Phase 1; a
   `POST /api/questions/<id>/upload-image/` endpoint + drag-and-drop UI is
   the next slice.

5. **Browse/Question-Bank chapter filter UI.** Backend supports `?chapter=`
   already; the chapter selector isn't in the QuestionBank filter bar yet
   (Browse has Subject + Grade only). Small frontend follow-up; M7-03's
   remaining slice.

6. **`pylon` SMS** — deliberately not ported. If SMS is ever needed, wire a
   modern provider (Twilio / MSG91) behind a new `apps/sms/` shim with the
   same Celery hook points as `emails.py`. Out of scope until product asks.

7. **`ink.Dossier` CRM fields** (secondary email/phone, `flagged`) —
   deliberately not ported. Legacy CRM workflow lived in Django admin and
   has no modern user-facing equivalent.

## Activation checklist before retiring a legacy app

When the urge to delete `legacy_app/` strikes:

- [ ] Confirm every row in the matching "by audience" table above is ✅ (or
  ⛔ with a reason captured here).
- [ ] Run `audit_cabinet_fidelity --strict` (cabinet) or the relevant
  parity test, if one exists.
- [ ] `git grep -F "from <legacy_app>" backend/` returns zero hits.
- [ ] Migration plan for any `legacy_app` rows still in the production DB
  (most teams retain them as a read-only archive — fine).
- [ ] Open a PR titled `chore: retire legacy <name>` that deletes the
  package and updates this doc's row to ⛔ with a "retired YYYY-MM-DD #N" tag.

## How this audit was produced

A pass over each legacy app's `models.py` + `views.py` (where present)
against the modern `backend/openshiksha/apps/<name>/` and `frontend_modern/
src/features/`. Where CLAUDE.md already had a definitive answer (the
"Already ported" table in the routine prompt), this doc mirrors it; where it
was silent or out-of-date, the legacy code was the source of truth.
