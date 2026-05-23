# 2026-05-22 — Activity Streaks, Question Content Search, Remedial Auto-Creation

## Summary

Three features shipped in one PR (#84): the first gamification mechanic (activity streaks), a one-line search improvement, and the formative-assessment loop (remedial assignments).

## Classification

- **Activity Streaks**: New (no gamification existed in legacy)
- **Question Content Search**: Improve (legacy had no web search)
- **Remedial Auto-Creation**: Port + Improve (legacy grader had this; modern version improves targeting)

## Legacy Reference

- `grader/` — Legacy auto-created remedials for students scoring < 30% using `GenericFK` on Assignment; created a copy of the full problem set
- No legacy streak or gamification feature existed
- No legacy question content search (Cabinet filesystem, browsed by chapter)

## What's Different from Legacy

### Remedial (Improved)
- Legacy: full problem set copy → Modern: only wrong questions (mark < 1.0)
- Legacy: `GenericFK` (class or student target) → Modern: SubjectRoom FK (cleaner, O(1) queries)
- Legacy threshold hardcoded, no visibility → Modern: named constant `REMEDIAL_THRESHOLD = 0.30`, admin-visible `is_remedial` flag, `source_assignment` audit trail

## Technical Details

### Backend

**New model — `StudentStreak`** (`core/models.py`):
- `OneToOneField` to `User` — O(1) lookup, no aggregation
- `record_activity(date)` encapsulates streak logic on the model (testable in isolation)
- Same-day idempotency guard: returns early if `activity_date == last_activity_date`
- `update_fields` save avoids full row write

**New signal — `update_student_streak`** (`core/signals.py`):
- Mirrors `trigger_grading_on_submit` guard exactly (fires on `submitted_at` explicit save)
- `get_or_create` to handle first submission without pre-created streak row

**New API action — `me_streak`** (`api/views/core.py`):
- `GET /api/v1/users/me/streak/` — students only (403 for teachers/parents)
- Returns `current_streak`, `longest_streak`, `last_activity_date`

**Search improvement** (`api/views/core.py`):
- `QuestionViewSet.search_fields` += `subparts__question_text`, `tags__name`
- DRF `SearchFilter` handles DISTINCT automatically on M2M traversal

**New model fields — `ProblemSet`** (`core/models.py`):
- `is_remedial` BooleanField (default=False)
- `source_assignment` FK → Assignment (nullable, SET_NULL)

**Remedial helper — `_create_remedial_assignment`** (`core/tasks.py`):
- Called from `grade_submission` when `score < REMEDIAL_THRESHOLD`
- Idempotency: checks for existing remedial Assignment for same source + subject_room
- `number` auto-computed as `max(number) + 1` to satisfy `ProblemSet.unique_together`
- 3-day `due_at` from creation time

### Frontend

- `useStreak.ts` — React Query hook, `staleTime: 60s`
- `StudentDashboard.tsx` — streak badge (orange pill, shows "🔥 N-day streak · best: M" when M > N, hidden at streak=0)
- `AssignmentCard.tsx` — "Remedial Practice" amber badge when `problem_set.is_remedial`
- `types/index.ts` — `ProblemSet` interface updated with `is_remedial` + `source_assignment`

## Tests Written

| File | Tests | Description |
|------|-------|-------------|
| `test_streak.py` | 7 | record_activity state machine, me_streak endpoint |
| `test_remedial.py` | 3 | created below threshold, not created above, idempotent |
| `test_core_api.py` | 2 | search by subpart text, search by tag name |

**306 → 318 tests, 90.76% coverage**

## Migration Notes

`0005_add_student_streak_and_remedial_fields`:
- Non-breaking: new table + nullable fields on existing table
- `student_streaks`: created lazily on first submission or API call
- `problem_sets.is_remedial`, `problem_sets.source_assignment_id`: both have defaults, existing rows unaffected

## Next Steps

- Phase 2 streaks: grace day ("streak freeze"), milestone badges (7d/30d), SRS drill sessions count as activity
- Remedial Phase 2: per-student remedials (currently one per class); student-specific question targeting when multiple students fail the same assignment
- Notification when remedial is created (email/push)
- Streak leaderboard on teacher dashboard
