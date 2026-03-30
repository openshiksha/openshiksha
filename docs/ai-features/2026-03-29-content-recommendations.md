# AI-Powered Content Recommendations

**Category:** AI-Powered Content Recommendations (Category 5)
**Date:** 2026-03-29
**Branch:** `ai/2026-03-29-content-recommendations`
**PR:** openshiksha/openshiksha#60

---

## Problem It Solves

Students finishing an assignment don't know what to do next. They might re-do chapters they've already mastered, skip chapters where they're struggling, or simply stop practicing. Teachers can't manually curate individualised next-steps for every student every day.

This feature answers the question: **"What should I practice next?"** — automatically, for every student, in priority order.

---

## How It Works (Technical)

### App: `openshiksha.apps.ai` (extends existing app)

```
backend/openshiksha/apps/ai/
├── models.py        — adds ContentRecommendation, PracticePlan
├── analytics.py     — adds generate_recommendations_for_student(), build_practice_plan()
├── tasks.py         — adds refresh_recommendations_for_student, generate_daily_practice_plan
├── serializers.py   — adds ContentRecommendationSerializer, PracticePlanSerializer
├── views.py         — adds ContentRecommendationViewSet, PracticePlanViewSet
├── urls.py          — registers new routes
├── admin.py         — registers new models
└── migrations/
    └── 0002_content_recommendations_practice_plans.py
```

### Recommendation Algorithm (`generate_recommendations_for_student`)

Pure heuristic — no external ML or LLM dependency. Runs in-process, offline.

**Priority ladder (lower number = more urgent):**

| Priority | Reason | Trigger |
|----------|--------|---------|
| 1 — URGENT | `severe_gap` | Active LearningGap with avg_score < 25% |
| 2 — HIGH | `moderate_gap` | Active LearningGap with avg_score 25–40% |
| 2 — HIGH | `spaced_review` | LearningGap resolved within last 7 days |
| 3 — MEDIUM | `mild_gap` | Active LearningGap with avg_score 40–50% |
| 4 — LOW | `next_topic` | Chapter with no ticks yet (unvisited), ordered by `chapter.order` |

**Deduplication:** Each chapter appears at most once per run. Gap-based reasons take precedence over next_topic.

**Problem set selection:** For each recommendation, the engine finds the best problem set to attempt:
1. An already-assigned ProblemSet in the chapter that the student hasn't submitted yet
2. Fall back to the lowest-numbered active ProblemSet in the chapter

### Practice Plan Assembly (`build_practice_plan`)

Takes the sorted recommendation list, slices the top 5 (configurable via `MAX_PLAN_RECOMMENDATIONS`), and computes `estimated_minutes`:
- Uses `ProblemSet.estimated_minutes` when available
- Falls back to `DEFAULT_MINUTES_PER_REC = 10` minutes per recommendation

### Celery Tasks

| Task | Trigger | Idempotent |
|------|---------|-----------|
| `refresh_recommendations_for_student(student_id, room_id)` | After grading; or on-demand via API | Yes — deactivates stale, upserts fresh |
| `generate_daily_practice_plan(student_id, room_id)` | After recommendations refresh | Yes — update_or_create by (student, room, date) |
| `analyze_student_subject_room(student_id, room_id)` | Already existed; now also enqueues recommendations | Yes |

### API Endpoints

| Method | URL | Who | Description |
|--------|-----|-----|-------------|
| GET | `/api/v1/ai/recommendations/` | Student | Active recommendations sorted by priority |
| GET | `/api/v1/ai/recommendations/{id}/` | Student | Single recommendation detail |
| POST | `/api/v1/ai/recommendations/{id}/action/` | Student | Mark as actioned (opened problem set) |
| GET | `/api/v1/ai/practice-plans/` | Student | All practice plans (history) |
| GET | `/api/v1/ai/practice-plans/today/` | Student | Today's plan |
| POST | `/api/v1/ai/trigger/recommendations/` | Student | Trigger refresh + plan generation |

Query params on `GET /recommendations/`:
- `?include_inactive=true` — show superseded recommendations too

---

## Models Created

### `ContentRecommendation`

```python
student          FK → User
subject_room     FK → SubjectRoom
chapter          FK → Chapter
problem_set      FK → ProblemSet (nullable)
reason           choices: severe_gap | moderate_gap | mild_gap | spaced_review | next_topic
priority         int: 1=urgent, 2=high, 3=medium, 4=low
score_snapshot   float (0–1) — avg_score when generated, null for next_topic
is_actioned      bool — student has opened/started the problem set
is_active        bool — False when superseded by re-analysis
generated_at     datetime
actioned_at      datetime (nullable)
```

Unique constraint: `(student, chapter, subject_room)` — one active rec per chapter per context.

### `PracticePlan`

```python
student          FK → User
subject_room     FK → SubjectRoom
plan_date        date
recommendations  M2M → ContentRecommendation
estimated_minutes int
is_completed     bool
generated_at     datetime
```

Unique constraint: `(student, subject_room, plan_date)` — one plan per day per context.

---

## User Impact

### Students
- See a prioritised "what to practice next" list without needing to figure it out themselves
- Daily practice plan tells them exactly how many minutes to budget
- Marking a recommendation as "actioned" removes it from the urgent view
- Spaced review nudges them back to chapters they recently fixed (preventing regression)

### Teachers
- Students self-direct remediation based on real gap data — less "what should I do?" questions
- Gap-driven recommendations mean students are doing targeted practice, not random work
- Future: teacher dashboard can show recommendation acceptance rates as a proxy for student engagement

### Parents
- Can ask "what is my child supposed to work on today?" and get a specific answer via the practice plan
- Estimated minutes gives realistic expectations for homework time

---

## Future Enhancements

1. **Collaborative filtering:** "Students similar to you (same grade, similar gap profile) benefited from practicing X" — cross-student recommendation signal
2. **LLM-generated rationales:** Add a `rationale` field with a plain-language explanation ("You got 3 out of 10 correct on Fractions last week. Let's try the next set.")
3. **Acceptance rate analytics:** Track `is_actioned` rates per chapter to identify chapters students consistently skip (may signal content quality issues)
4. **Parent push notifications:** Daily plan summary sent to parents via FCM/SMS
5. **Difficulty adaptation:** When a student keeps getting `spaced_review` for the same chapter, suggest a lower-difficulty problem set

---

## Dependencies

- Builds on: `LearningGap` (from 2026-03-28 Smart Analytics feature)
- Reads: `Tick` data via `detect_gaps_for_student` (same source as gap detection)
- Writes: `ContentRecommendation`, `PracticePlan`
- No external ML/LLM APIs required — fully offline heuristic
