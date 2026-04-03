# Adaptive Learning Engine

**Category:** Adaptive Learning Engine (Category 1)
**Date:** 2026-03-30
**Branch:** `ai/2026-03-30-adaptive-learning-engine`
**PR:** openshiksha/openshiksha#62

---

## Problem It Solves

Students currently receive the same assignments in the same order regardless of what they already know. A student who has mastered fractions still gets fraction homework. A student who is struggling with linear equations gets assigned quadratic equations before they are ready. There is no memory of what was learned last week — forgetting is invisible.

This feature answers three questions automatically, for every student:

1. **What order should I study chapters in?** — respecting curriculum prerequisites
2. **What can I skip?** — chapters already mastered (score ≥ 80%)
3. **What should I review?** — chapters I learned before but need to refresh (spaced repetition)

---

## How It Works (Technical)

### App: `openshiksha.apps.ai` (extends existing app)

```
backend/openshiksha/apps/ai/
├── adaptive_analytics.py    — pure computation (no DB writes)
│     compute_updated_mastery()        EWMA mastery scoring
│     compute_srs_update()             SM-2 spaced repetition
│     get_due_srs_entries()            SRS lookahead query
│     generate_learning_path_steps()   path generation (topo-sort + SRS)
│     _topological_sort_nodes()        Kahn's algorithm (cycle-safe)
├── models.py                — adds 5 new models (see below)
├── tasks.py                 — adds 4 new Celery tasks
├── serializers.py           — adds 6 new serializers
├── views.py                 — adds 4 new viewsets
├── urls.py                  — registers new routes
├── admin.py                 — registers new models
├── migrations/
│   └── 0003_adaptive_learning_engine.py
└── tests/
    └── test_adaptive_learning.py      42 tests
```

---

### Models

#### `KnowledgeNode`
Represents a chapter as a node in the prerequisite knowledge graph. One node per `(subject, chapter)` pair — shared across all students. Edges are curated by teachers/admins via Django admin.

```python
KnowledgeNode
  subject → Subject
  chapter → Chapter
  prerequisites ↔ KnowledgeNode (M2M, directed)
  difficulty_weight: float (0.1–5.0, affects SRS interval scaling)
```

#### `StudentMastery`
Tracks a student's mastery level for a KnowledgeNode using an Exponentially Weighted Moving Average (EWMA).

```python
StudentMastery
  student → User
  knowledge_node → KnowledgeNode
  mastery_score: float (EWMA, α=0.3)
  mastery_level: unknown | novice | developing | proficient | mastered
  attempt_count: int
  last_attempted_at / first_attempted_at: datetime
```

**Mastery levels:**

| Level | Score range |
|-------|------------|
| unknown | No attempts |
| novice | 0–39% |
| developing | 40–59% |
| proficient | 60–79% |
| mastered | 80%+ |

#### `SpacedRepetitionEntry`
SM-2-inspired scheduling. After each practice session the interval is updated — successful recall makes the interval grow; failure resets it to 1 day.

```python
SpacedRepetitionEntry
  student → User
  knowledge_node → KnowledgeNode
  interval_days: int
  easiness_factor: float (1.3–5.0, controls interval growth rate)
  repetitions: int (consecutive successful recalls)
  next_review_date: date
```

**SM-2 update rules:**
- Score ≥ 0.60 (success): `new_interval = prev_interval × EF`; EF increases
- Score < 0.60 (failure): `interval = 1`, `repetitions = 0`; EF unchanged

#### `LearningPath`
A personalised, ordered sequence of KnowledgeNodes for a student to work through. Only one `ACTIVE` path per `(student, subject_room)` at a time. Rebuilt after every grading event.

```python
LearningPath
  student → User
  subject_room → SubjectRoom
  status: active | completed | stale
  total_steps / completed_steps: int
```

#### `LearningPathStep`
A single step in a LearningPath — one chapter to study or review.

```python
LearningPathStep
  learning_path → LearningPath
  knowledge_node → KnowledgeNode
  problem_set → ProblemSet (optional, suggested)
  position: int (1-indexed)
  status: pending | in_progress | completed | skipped
  is_review: bool (True = inserted by SRS scheduler)
  score_when_completed: float
```

---

### Path Generation Algorithm (`generate_learning_path_steps`)

1. Load all active `KnowledgeNode`s for the subject
2. Load the student's current `StudentMastery` scores
3. **Filter**: remove nodes where `mastery_score ≥ 0.80` (mastered → skip)
4. **Topological sort** remaining nodes by prerequisite edges (Kahn's algorithm)
   - Ties broken by `chapter.order` (curriculum sequence)
   - Cycle-safe: cycle residue appended by `chapter.order`
5. **Interleave SRS reviews**: fetch nodes due for review within 3 days
   - Already-mastered nodes due for review → injected as review steps at position 1, 2, ...
   - Unmastered nodes that are also SRS-due → flagged `is_review=True` in their natural position
6. Suggest a `problem_set` for each step (prefers unsubmitted assigned sets)

---

### Celery Task Chain

```
After grading (analyze_student_subject_room):
  └─ update_student_mastery(student_id, subject_room_id)
  └─ rebuild_learning_path(student_id, subject_room_id)

After step completion (complete_learning_path_step):
  └─ update_spaced_repetition_for_student(student_id, node_id, score)
  └─ update_student_mastery(student_id, subject_room_id)
  └─ rebuild_learning_path(student_id, subject_room_id)   [unless path completed]
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/ai/knowledge-nodes/` | Prerequisite graph (filter: `?subject_id=`) |
| GET | `/api/v1/ai/knowledge-nodes/{id}/` | Single node |
| GET | `/api/v1/ai/mastery/` | Student's mastery levels (filter: `?mastery_level=`) |
| GET | `/api/v1/ai/mastery/{id}/` | Single mastery record |
| GET | `/api/v1/ai/spaced-repetition/` | All SRS entries |
| GET | `/api/v1/ai/spaced-repetition/due/` | Entries due within 3 days |
| GET | `/api/v1/ai/learning-paths/` | All paths (history) |
| GET | `/api/v1/ai/learning-paths/active/` | Current active path with steps |
| POST | `/api/v1/ai/learning-paths/rebuild/` | Trigger regeneration `{subject_room_id}` |
| POST | `/api/v1/ai/learning-paths/steps/{id}/complete/` | Mark step done `{score}` |

---

## Models / APIs Created

- **5 new DB tables**: `ai_knowledge_nodes`, `ai_student_mastery`, `ai_learning_paths`, `ai_learning_path_steps`, `ai_spaced_repetition_entries`
- **4 new Celery tasks**: `update_student_mastery`, `update_spaced_repetition_for_student`, `rebuild_learning_path`, `complete_learning_path_step`
- **4 new API viewsets**: `KnowledgeNodeViewSet`, `StudentMasteryViewSet`, `SpacedRepetitionViewSet`, `LearningPathViewSet`
- **1 new analytics module**: `adaptive_analytics.py`
- **Migration**: `0003_adaptive_learning_engine.py`

---

## User Impact

| User | Impact |
|------|--------|
| **Students** | Always know the next step; never redo mastered content; SRS prevents forgetting; path respects what they're ready for |
| **Teachers** | Knowledge graph curated once in admin; all students benefit from correct prerequisite edges; mastery levels give richer insight than raw scores |
| **Parents** | Mastery levels (novice → mastered) give a clear, grade-independent view of what the child has actually learned vs. just attempted |

---

## Future Enhancements

- **LLM-powered prerequisite suggestions**: auto-suggest prerequisites based on chapter names and curriculum metadata
- **Difficulty-adaptive problem selection**: within a step, prefer easier problems when mastery is low, harder when developing
- **Cross-subject paths**: detect prerequisites across subjects (e.g. arithmetic before algebra even if they're in different subjects)
- **Streak and momentum tracking**: reward consecutive daily steps to drive engagement
- **Teacher intervention hooks**: surface students whose path has been stalled for > 7 days

---

## Dependencies

- No external ML or LLM APIs — fully offline heuristics
- Requires `core.Chapter.order` field to be set for curriculum-correct ordering
- SRS and mastery are per `(student, knowledge_node)` — `KnowledgeNode`s must be created by an admin before the engine can generate paths
