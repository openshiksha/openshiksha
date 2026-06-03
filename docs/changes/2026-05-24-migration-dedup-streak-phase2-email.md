# 2026-05-24 — Migration Dedup, Streak Phase 2, Email Notifications

## Summary

Three PRs shipped: critical migration conflict fix (PR #88), streak grace day + milestone tiers (PR #89), and Phase 1 email notifications (PR #90).

## Classification

- **Migration dedup**: Fix (critical technical debt — two `core/0006` files from yesterday's dual-branch merge)
- **Streak Phase 2**: Improve (extends PR #84's minimal viable streak with psychological safety and aspirational progression)
- **Email Notifications Phase 1**: New (legacy used Pylon SMS; email is zero-dependency in dev, free to deploy in prod)

---

## PR #88 — Fix core/0006 migration conflict

### Problem
Both PR #86 (question images) and PR #87 (per-student remedials) were branched from `modernization` at the same commit, each created `core/0006` independently, then both merged. Result: two files named `0006` with `dependencies = [("core", "0005_...")]`, causing Django to see two leaf nodes in the migration graph. Any fresh `manage.py migrate` would fail with "Conflicting migrations".

### Fix
- Renamed `0006_add_assignment_target_student.py` → `0007_add_assignment_target_student.py`
- Updated its `dependencies` from `0005` → `0006_add_question_subpart_image_url`
- Verified via `MigrationLoader(None).graph.leaf_nodes('core')` returns a single leaf

### Files Changed
- `backend/openshiksha/apps/core/migrations/` (rename + edit)

---

## PR #89 — Streak Phase 2: Grace Day + Milestone Badges

### What Changed

#### Grace Day Mechanic
A gap of exactly 1 day no longer breaks the streak — it pauses it instead. One grace per streak run; consuming it sets `streak_grace_used=True`. A consecutive-day increment resets grace to `False`. A 2+ day gap (or a second 1-day gap with grace exhausted) resets the streak to 1.

**Model change**: `streak_grace_used = BooleanField(default=False)` on `StudentStreak`
**Migration**: `0008_add_streak_grace_day.py`
**API change**: `GET /api/v1/users/me/streak/` now returns `streak_grace_used` and `milestone_tier`

#### Milestone Tier System
`StudentStreak.milestone_tier` property (no DB column — computed from `current_streak`):
- `none` (< 3 days)
- `starter` (3–6 days)
- `week` (7–29 days)
- `month` (30–59 days)
- `champion` (60+ days)

#### Frontend StreakBadge Component
New `StreakBadge.tsx` replaces the hardcoded 🔥 in `StudentDashboard`. Tier-aware badge art:
- `starter`: 🔥 On Fire (orange)
- `week`: ⚡ Week Warrior (yellow)
- `month`: 🌟 Month Master (amber)
- `champion`: 👑 Champion (purple)
- Shows grace indicator when `graceUsed=true`

### What Changed From Legacy
No legacy equivalent — new gamification layer. The grace day mechanic follows Duolingo's post-2022 model: punish absences proportionally rather than catastrophically.

### Files Changed
- `backend/openshiksha/apps/core/models.py` — `StudentStreak` model
- `backend/openshiksha/apps/core/migrations/0008_add_streak_grace_day.py`
- `backend/openshiksha/apps/api/views/core.py` — `me_streak` endpoint
- `backend/openshiksha/apps/core/tests/test_streak.py` — 12 new tests, 1 updated
- `frontend_modern/src/features/student/useStreak.ts` — new types
- `frontend_modern/src/features/student/StreakBadge.tsx` — new component
- `frontend_modern/src/features/student/StudentDashboard.tsx` — uses StreakBadge

### Tests Written
| Test | Description |
|------|-------------|
| `test_grace_day_preserves_streak` | Day 1, skip 2, day 3 → streak=2, grace=True |
| `test_grace_day_only_once_per_run` | Second 1-day gap after grace → reset |
| `test_grace_day_resets_on_consecutive` | Consecutive after grace → grace=False |
| `test_two_day_gap_resets_streak` | 3-day gap always resets |
| `test_longest_streak_preserved_through_grace` | longest_streak correct through grace |
| `test_milestone_tier_*` | Boundary tests for all 5 tiers |
| `test_streak_response_includes_grace_and_tier` | API endpoint includes new fields |

---

## PR #90 — Email Notifications Phase 1

### What Changed

#### New module: `apps/core/emails.py`
Two helper functions:
- `notify_grading_complete(student, assignment_title, score_pct)` — subject: `"Your assignment has been graded: {N}%"`
- `notify_remedial_assigned(student, chapter_name, due_date_str)` — subject: `"You have a new practice assignment"`

Both guard against empty email, wrap `send_mail` in `try/except`, and log failures — email errors never propagate to grading logic.

#### Hooks in `tasks.py`
- `grade_submission`: calls `notify_grading_complete` after `submission.save()`
- `_create_remedial_assignment`: calls `notify_remedial_assigned` after `Assignment.objects.create()`

#### Settings
- Added `EMAIL_SUBJECT_PREFIX = "[OpenShiksha] "`
- Updated `DEFAULT_FROM_EMAIL` to `"OpenShiksha <noreply@openshiksha.edu.in>"`
- Dev: `EMAIL_BACKEND` defaults to console (zero setup — visible in `docker compose logs backend`)
- Prod: SMTP backend already configured in `production.py`

### What Changed From Legacy
Legacy `pylon/` sent SMS via a third-party API. Email is zero-dependency in dev and requires only SMTP credentials in prod. SMS can be added later via a modern provider.

### Files Changed
- `backend/openshiksha/apps/core/emails.py` — new
- `backend/openshiksha/apps/core/tasks.py` — two email hooks
- `backend/openshiksha/apps/core/tests/test_email_notifications.py` — new (6 tests)
- `backend/openshiksha/settings/base.py` — EMAIL_SUBJECT_PREFIX + DEFAULT_FROM_EMAIL

### Tests Written
| Test | Description |
|------|-------------|
| `test_notify_remedial_assigned_sends_email` | Helper sends correct subject/body/recipient |
| `test_notify_grading_complete_sends_email` | Helper sends score in subject |
| `test_no_email_if_no_email_address` | Both helpers skip silently when email=="" |
| `test_grading_complete_email_sent` | grade_submission task triggers email |
| `test_no_email_when_student_has_no_email` | Task skips email for students without address |
| `test_email_failure_does_not_break_grading` | Exception in send_mail doesn't break grading |

---

## Migration Notes

- `0007_add_assignment_target_student.py`: rename only — no schema change
- `0008_add_streak_grace_day.py`: adds `streak_grace_used BooleanField(default=False)` — non-breaking, all existing rows get `False`

**Note**: PRs #89 and #90 both cherry-pick the migration dedup fix from PR #88. When PR #88 merges to `modernization` first, the cherry-pick commits in #89 and #90 become effectively no-ops (same diff already applied).

## Test Counts
| Branch | Tests |
|--------|-------|
| Start of day (modernization) | 327 |
| After PR #88 | 327 (no new tests) |
| After PR #89 (streak-phase2) | 339 |
| After PR #90 (email-notifications) | 333 |
| After all 3 merge | ~345 (estimated) |

## Next Steps
- Streak milestone badges: consider milestone-crossing push notification (Phase 2)
- Email Phase 2: assignment due-date reminder (Celery beat, daily at 8am IST)
- Email preferences: per-student opt-out toggle in settings page (P3)
- Open student flow (P1 from task list) — browse by board/subject without classroom
