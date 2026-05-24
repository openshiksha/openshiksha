# 2026-05-23 — SRS Proficiency Integration, Question Image Support, Per-Student Remedials

## Summary

Three features shipped in three PRs: SRS drill sessions now feed into the proficiency engine and streak system (PR #85), questions can carry image URLs rendered in the student view (PR #86), and remedial assignments are now targeted at individual failing students instead of the entire class (PR #87).

## Classification

- **SRS → Proficiency + Streak**: Improve (closes data consistency gap — drills updated SM-2 but left proficiency scores and streaks unchanged)
- **Question Image Support**: Improve (legacy Cabinet stored base64 images on an external filesystem; modern version uses URL references)
- **Per-Student Remedials**: Improve (yesterday's Port was class-wide; this makes it per-student, matching the legacy system's user-targeted mode without GenericFK complexity)

## Legacy Reference

- `grader/` — per-student remedial pattern (GenericFK targeting User vs SubjectRoom)
- `cabinet/cabinet_api.py` — `build_image()` base64 image storage
- No legacy SRS — the proficiency bridge is new infrastructure

## What Changed From Legacy and Why

### SRS → Proficiency + Streak (PR #85)

**Problem**: `mark_reviewed` in `ai/views.py` graded answers and updated the SM-2 schedule but never created `Tick` records or called `update_proficiency`. A student who mastered algebra through daily drills still showed 45% in the proficiency bar. The same issue applied to streaks — SRS drills didn't count.

**Fix**:
- `Tick.submission` made nullable (migration `edge/0003`) — SRS drills have no `Submission` row
- `mark_reviewed` grading loop refactored to capture per-subpart fractions in one pass (avoids double `_grade_subpart` call)
- After SM-2 update: `Tick.bulk_create()` for answered subparts, `update_proficiency.delay()` queued for the student's SubjectRoom (graceful no-op if no SubjectRoom found — handles open students)
- `StudentStreak.record_activity()` called after every drill session (idempotent — same-day calls are no-ops)

### Question Image Support (PR #86)

**Problem**: ~30-40% of CBSE science and math questions include diagrams. `QuestionSubpart` had no image field, blocking real question bank content.

**Fix**:
- `image_url = URLField(max_length=2000, blank=True, default="")` on `QuestionSubpart` (migration `core/0006`)
- Exposed in both `QuestionSubpartSerializer` (teacher) and `QuestionSubpartStudentSerializer` (student)
- `QuestionCard.tsx`: renders `<img>` above question text with `loading="lazy"`, `maxHeight: 320px`, `objectFit: contain`, `onError` hides broken images silently
- `CreateQuestionPage.tsx`: per-subpart `image_url` input with live inline preview
- Admin `QuestionSubpartInline` updated to include `image_url` and `options` fields

### Per-Student Remedials (PR #87)

**Problem**: Yesterday's remedial auto-creation (PR #84) created one `Assignment(subject_room=...)` class-wide. All students saw "Remedial Practice" when any student failed — confusing and incorrect.

**Fix**:
- `target_student` nullable FK on `Assignment` (migration `core/0006`) — `null` means class-wide (unchanged for all existing assignments)
- `_create_remedial_assignment` idempotency check is now per-student + source assignment (not per room)
- `target_student=submission.student` set on the created remedial Assignment
- `AssignmentViewSet.get_queryset()` for students: `Q(target_student=None) | Q(target_student=user)` — students only see class-wide or their own targeted assignments
- `AssignmentSerializer` exposes `target_student`; admin updated

## Technical Details

### Backend — migrations created (all non-breaking)
- `edge/0003_make_tick_submission_nullable.py` — `Tick.submission` nullable
- `core/0006_add_question_subpart_image_url.py` — `QuestionSubpart.image_url` (P2 branch)
- `core/0006_add_assignment_target_student.py` — `Assignment.target_student` (P3 branch, same number as P2 since branched independently)

### Frontend changes
- `types/index.ts` — `QuestionSubpart.image_url?: string`, `QuestionSubpartWrite.image_url?: string`
- `QuestionCard.tsx` — image render block above question text
- `CreateQuestionPage.tsx` — `SubpartDraft.image_url`, URL input, live preview

## Tests Written

| PR | File | New Tests | Description |
|----|------|-----------|-------------|
| #85 | `test_srs_drill_api.py` | 4 | Tick creation, streak update, streak idempotency, graceful fallback |
| #86 | `test_core_api.py` | 2 | image_url in API response, default empty string |
| #87 | `test_remedial.py` | 4 | target_student set, passing student visibility, two students two Assignments, idempotency |

**Baseline**: 318 (start of day)
**After P1 (#85)**: 322
**After P2 (#86)**: 320 (branched from modernization, not from P1)
**After P3 (#87)**: 321 (branched from modernization, not from P1/P2)

When all three PRs merge to `modernization`, the combined count will be ~330+.

## Migration Notes

All migrations are non-breaking:
- `Tick.submission` nullable: existing rows have a submission FK, unaffected
- `QuestionSubpart.image_url`: all existing rows get `""` (empty string default)
- `Assignment.target_student`: all existing assignments get `null` (class-wide, unchanged behaviour)

Note: `core/0006` is used for two separate migrations on separate branches. When both PRs merge, one will need to be renumbered to `0007`. The merge order determines which gets renumbered.

## Next Steps

- Streak Phase 2: grace day ("streak freeze"), milestone badges (7d/30d/60d)
- Phase 1 email notifications: remedial created → email student; grading complete → email student
- Open student flow (P1 from task list) — browse by board/subject without classroom
- Image upload endpoint (Phase 2) — replace URL-based approach with Django media upload
- Migrate legacy Cabinet questions to new DB schema (image import path)
