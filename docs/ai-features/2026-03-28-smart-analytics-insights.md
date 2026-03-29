# Smart Analytics & Insights

**Category:** Smart Analytics & Insights (Category 4)
**Date:** 2026-03-28
**Branch:** `ai/2026-03-28-smart-analytics-insights`
**PR:** openshiksha/openshiksha#55

---

## Problem It Solves

Students don't know *where* they are weak — they just know they got a bad score. Teachers can't tell at a glance which chapters are causing the most difficulty for their class. There's no signal that connects practice data to actionable next steps.

This feature mines existing `Tick` data to surface three kinds of insight automatically:

1. **Per-student learning gaps** — exactly which chapters a student is underperforming in, with severity
2. **Class-level insights** — which chapters are hardest for the class as a whole
3. **Exam-readiness prediction** — a heuristic forecast of how ready a student is for assessment

---

## How It Works (Technical)

### App: `openshiksha.apps.ai`

```
backend/openshiksha/apps/ai/
├── models.py       — LearningGap, ClassInsight, PerformancePrediction
├── analytics.py    — Pure computation algorithms (no DB writes)
├── tasks.py        — Celery tasks (idempotent upserts, retry logic)
├── serializers.py  — DRF serializers
├── views.py        — DRF viewsets with role-based filtering
├── urls.py         — Router registration
├── admin.py        — Django admin
└── tests/
    └── test_analytics.py  — 27 tests (unit + integration)
```

### Learning Gap Detection (`detect_gaps_for_student`)

```
For each chapter where student has ticks:
  avg_score = total_marks / tick_count   (requires ≥ 3 ticks)

  if avg_score < 0.50:  → gap detected
    severity:
      severe:   avg_score < 0.25
      moderate: 0.25 ≤ avg_score < 0.40
      mild:     0.40 ≤ avg_score < 0.50

  if avg_score ≥ 0.60:  → previously detected gap resolved
```

### Class Insight Generation (`generate_insights_for_subject_room`)

```
For each (student, chapter) pair in the SubjectRoom:
  compute per-student chapter avg_score from ticks

Group by chapter → list of per-student scores
  students_struggling = count(score < 0.50)
  pct_struggling = students_struggling / students_assessed

  insight_type:
    struggling: pct > 0.40
    at_risk:    pct > 0.20
    proficient: pct ≤ 0.20

(Requires ≥ 2 students assessed per chapter)
```

### Performance Prediction (`predict_performance_for_student`)

```
Split all ticks into:
  recent: created in last 30 days   (weight 2×)
  older:  created before cutoff     (weight 1×)

weighted_score = (2 × Σrecent_marks + Σolder_marks) / (2×|recent| + |older|)

confidence = sigmoid((tick_count / 20) - 2)
  → low when data is sparse (< ~10 ticks)
  → high when data is rich  (> ~30 ticks)

trend:
  improving:  recent_avg - older_avg > 0.05
  declining:  recent_avg - older_avg < -0.05
  stable:     otherwise

readiness_level:
  needs_attention: predicted < 0.40
  developing:      0.40 ≤ predicted < 0.65
  on_track:        0.65 ≤ predicted < 0.80
  exam_ready:      predicted ≥ 0.80
```

### Data Flow

```
Grading completes (Submission graded)
  → enqueue analyze_student_subject_room.delay(student_id, subject_room_id)
  → enqueue generate_class_insights_for_subject_room.delay(subject_room_id)
        ↓
  Celery workers scan Ticks
        ↓
  Upsert LearningGap / ClassInsight / PerformancePrediction rows
        ↓
  API serves cached results to students + teachers
```

---

## Models / APIs Created

### Models

| Model | DB Table | Purpose |
|-------|----------|---------|
| `LearningGap` | `ai_learning_gaps` | Per-student per-chapter weakness |
| `ClassInsight` | `ai_class_insights` | Per-SubjectRoom per-chapter class insight |
| `PerformancePrediction` | `ai_performance_predictions` | Per-student per-SubjectRoom readiness |

### API Endpoints (`/api/v1/ai/`)

| Method | URL | Who | Purpose |
|--------|-----|-----|---------|
| GET | `learning-gaps/` | Student | Own active learning gaps |
| GET | `learning-gaps/?include_resolved=true` | Student/Teacher | Include resolved gaps |
| GET | `class-insights/` | Teacher | All insights for teacher's rooms |
| GET | `class-insights/by-room/{id}/` | Teacher/Student | Insights for specific room |
| GET | `predictions/` | Student | Own performance predictions |
| POST | `trigger/student/` | Student | Queue personal re-analysis |
| POST | `trigger/class/` | Teacher | Queue class re-analysis |

---

## User Impact

### Students
- See a ranked list of chapters to study: "You're struggling with Fractions (32% avg), Decimals (41% avg)"
- Get a readiness level before exams: "On Track — 71% predicted score in Mathematics"
- See their trend: "Improving — your recent work is 18% better than your older work"

### Teachers
- See class-level heatmap: "73% of your class is struggling with Trigonometry"
- Identify intervention targets without manual analysis
- Get quantitative data to inform lesson planning

### Parents (future)
- Can be shown prediction + trend data for their child's subjects
- Foundation for the Parent Intelligence Dashboard (future AI feature)

---

## Future Enhancements

1. **Trigger automation**: Wire up `analyze_student_subject_room` to the grading Celery task signal (currently must be triggered manually or via API)
2. **Chapter-level drill-down**: Surface which *question types* within a chapter are hardest
3. **Spaced repetition scheduling**: Use gap detection to schedule review assignments
4. **Notification hooks**: Alert student/parent when a new severe gap is detected
5. **LLM-powered explanations**: Replace heuristic trend descriptions with natural language summaries
6. **Confidence improvement**: Use Bayesian updating instead of simple sigmoid for confidence scores
7. **Cross-subject prediction**: Factor in inter-subject correlations (e.g. algebra skill predicts physics performance)

---

## Dependencies

- **Requires**: `openshiksha.apps.edge.Tick` data to exist (produced by grading pipeline)
- **Requires**: `openshiksha.apps.core.QuestionSubpart → Question → Chapter` chain to be intact
- **No external APIs** — pure heuristics, works offline
- **Celery + Redis** — required for async task execution (already configured)

---

## Running Tests

```bash
cd backend

# All 27 tests (unit + integration, SQLite)
pytest openshiksha/apps/ai/tests/test_analytics.py --ds=openshiksha.settings.test -v

# Django system check
python manage.py check

# Verify no missing migrations
python manage.py makemigrations --check
```
