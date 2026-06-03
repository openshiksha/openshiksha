# AI Pipeline Activation — 2026-04-04

## Summary

Activates the AI analytics engine end-to-end. The backend AI subsystem (learning gap detection, content recommendations, practice plans, class insights, mastery tracking, learning paths, spaced repetition) was fully built but never triggered — no submission had ever caused any AI task to run. This PR wires grading to the AI pipeline and surfaces results to both students and teachers.

## Classification

**New** — the AI engine existed in isolation; these changes activate it and add the first frontend surfaces.

## What Changed

### Backend

**`apps/core/tasks.py` — `grade_submission`**

Added two async task calls at the end of `grade_submission`, after proficiency update:

```python
analyze_student_subject_room.delay(submission.student_id, subject_room.id)
generate_class_insights_for_subject_room.delay(subject_room.id)
```

Every graded submission now automatically triggers the full AI analytics pipeline for the student, and recalculates class-level chapter health for the subject room.

**`apps/ai/tasks.py` — `analyze_student_subject_room`**

Added `generate_daily_practice_plan.delay(student_id, subject_room_id)` to the convenience task. Previously, recommendations were computed but never bundled into a `PracticePlan`. Now a daily practice plan is generated automatically every time analysis runs.

**`/api/ai/` URL prefix** — already registered in `apps/api/urls.py`. No change needed.

### Frontend (Student)

**`features/student/useRecommendations.ts`** — React Query hook for `GET /api/ai/recommendations/`. Fetches active `ContentRecommendation` records for the logged-in student, ordered by priority.

**`features/student/usePracticePlan.ts`** — React Query hook for `GET /api/ai/practice-plans/today/`. Returns today's `PracticePlan` or `null` if none exists yet (404 is handled gracefully, not surfaced as an error).

**`features/student/RecommendationsPanel.tsx`** — "What to Practice Next" panel rendered below the assignment list on `StudentDashboard`. Shows each recommendation with a priority badge (URGENT/HIGH/MEDIUM/LOW), chapter name, reason text, and score snapshot. Includes today's estimated practice minutes from the `PracticePlan`. Panel is hidden entirely when no recommendations exist — no empty state clutter.

**`features/student/StudentDashboard.tsx`** — imports and renders `<RecommendationsPanel />` below the assignment list.

### Frontend (Teacher)

**`features/teacher/useClassInsights.ts`** — React Query hook for `GET /api/ai/class-insights/?subject_room=<id>`. Accepts an `enabled` flag so the query only fires when the panel is expanded (lazy fetch).

**`features/teacher/ClassHealthPanel.tsx`** — Collapsible "Class Health" panel rendered inside each subject room card on `TeacherDashboard`. Expands to a table showing chapter name, class average score, number of struggling students, and a status indicator (🔴 Struggling / 🟡 At Risk / 🟢 Proficient). Includes a "Refresh" button that calls `POST /api/ai/trigger/class/` and re-fetches after 2 seconds. Empty state shown when no submissions exist yet.

**`features/teacher/TeacherDashboard.tsx`** — renders `<ClassHealthPanel subjectRoomId={room.id} />` inside each subject room card.

## No Legacy Equivalent

The original platform had no AI analytics. The only "personalization" was remedial assignments auto-created for scores < 30%. Everything in this PR is net-new educational capability.

## Tests Written

**`apps/core/tests/test_ai_pipeline_trigger.py`** (3 new tests):
- `test_grade_submission_triggers_ai_tasks` — verifies `analyze_student_subject_room.delay` and `generate_class_insights_for_subject_room.delay` are called after grading
- `test_grade_submission_ai_tasks_called_with_correct_ids` — verifies correct `student_id` / `subject_room_id` are passed
- `test_analyze_student_subject_room_dispatches_all_subtasks` — verifies all 6 sub-tasks are dispatched including `generate_daily_practice_plan`

All 254 backend tests pass. Frontend: type-check clean, lint clean, 11 Vitest tests pass.

## Architecture Notes

- AI tasks are fully decoupled from grading via Celery. If an AI task fails, grading is unaffected — the task retries independently (max 3 retries, 60s delay).
- In development (`CELERY_TASK_ALWAYS_EAGER=True`), all tasks run synchronously in the same process. In production, they run asynchronously via the Celery worker.
- The `ClassHealthPanel` uses lazy React Query (`enabled: isExpanded`) so class insight data is only fetched when the teacher actually opens the panel.

## Next Steps

- Croupier Phase 2: variable substitution (`{{x}}` token support in question text)
- Teacher analytics: surface `SubjectRoomQuestionMistake` data in assignment detail
- Spaced repetition UI: surface `LearningPath` / `SpacedRepetitionEntry` to students
- Parent dashboard
