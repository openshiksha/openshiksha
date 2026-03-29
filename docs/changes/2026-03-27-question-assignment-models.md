# Question Bank + Assignment Pipeline Models

**Date**: 2026-03-27
**Branch**: `feat/2026-03-27-question-assignment-models`
**PR**: https://github.com/openshiksha/openshiksha/pull/54
**Classification**: **Improve** — preserves legacy concepts, significantly upgrades implementation

---

## Summary

Adds the complete educational data layer to OpenShiksha: question bank, subject rooms, assignment pipeline, and submission tracking. This is the foundational work that makes the platform actually do something educational.

**7 new models · 6 new API endpoints · 30+ tests · 1 migration**

---

## Models Added

### Question Bank

| Model | Purpose |
|-------|---------|
| `QuestionTag` | Categorized tags (concept / skill / difficulty / special) |
| `Question` | Question with type, difficulty, soft delete, school/shared bank |
| `QuestionSubpart` | Subpart with JSONField `correct_answer` |
| `SubjectRoom` | Subject-specific classroom grouping |

### Assignment Pipeline

| Model | Purpose |
|-------|---------|
| `ProblemSet` | Curated question list (replaces `AssignmentQuestionsList`) |
| `Assignment` | Assignment of a ProblemSet to a SubjectRoom |
| `Submission` | Student's answers and grading state |

---

## Key Improvements Over Legacy

### Question
| | Legacy | Modern |
|-|--------|--------|
| Question types | MCQ only (enforced by Cabinet) | 5 types: MCQ, fill_blank, matching, multi_select, numeric |
| Difficulty | Derived from tags (hacky, implicit) | Explicit `difficulty` int field (1–5) |
| Soft delete | Hard delete or never deleted | `is_active` flag |
| Answer storage | Only in Cabinet (external service) | `correct_answer` JSONField in `QuestionSubpart` — enables offline grading |

### Assignment / ProblemSet
| | Legacy | Modern |
|-|--------|--------|
| Target (who gets assigned) | GenericFK to SubjectRoom OR User OR Remedial | Direct `subject_room` FK — simpler, faster, filterable |
| Time estimate | None | `estimated_minutes` on `ProblemSet` |
| Naming | `AssignmentQuestionsList` | `ProblemSet` — cleaner |

### Submission
| | Legacy | Modern |
|-|--------|--------|
| Answer storage | Only in Cabinet | `answers` JSONField — enables re-grading without Cabinet |
| In-progress state | Submit was all-or-nothing | `submitted_at` nullable — student can save progress |
| Score naming | `marks` (confusing) | `score` — clarifies it's a fraction (0–1) |

### SubjectRoom
| | Legacy | Modern |
|-|--------|--------|
| Uniqueness | No constraint | `unique_together = [classroom, subject]` |
| Archiving | No way to archive | `is_active` for year-end without deletion |

---

## API Endpoints

| Endpoint | Method | Who |
|----------|--------|-----|
| `/api/question-tags/` | GET | All authenticated |
| `/api/questions/` | GET | All authenticated (filtered by school) |
| `/api/subject-rooms/` | GET/POST/PUT/DELETE | Teachers (own rooms), students (enrolled) |
| `/api/problem-sets/` | GET | All authenticated |
| `/api/assignments/` | GET | Teachers (created by them) / Students (enrolled) |
| `/api/assignments/` | POST | Teachers only |
| `/api/assignments/{id}/submissions/` | GET | Teacher only |
| `/api/submissions/` | GET/POST/PATCH | Students (own submissions) |

---

## Files Changed

**Modified:**
- `backend/openshiksha/apps/core/models.py` — 7 new models added
- `backend/openshiksha/apps/core/admin.py` — admin for all new models
- `backend/openshiksha/apps/api/urls.py` — ViewSet router registrations

**Created:**
- `backend/openshiksha/apps/api/serializers/__init__.py`
- `backend/openshiksha/apps/api/serializers/core.py`
- `backend/openshiksha/apps/api/views/core.py`
- `backend/openshiksha/apps/core/migrations/0002_question_questiontag_subjectroom_questionsubpart_and_more.py`
- `backend/openshiksha/apps/core/tests/test_question_models.py`
- `backend/openshiksha/apps/core/tests/test_assignment_models.py`
- `backend/openshiksha/apps/api/tests/test_assignment_api.py`
- `backend/pytest.ini`

---

## Tests

### Model tests (`core/tests/`)
- `test_question_models.py`: QuestionTag uniqueness, Question difficulty validation (1–5), subpart ordering, cascade delete, SubjectRoom unique_together
- `test_assignment_models.py`: ProblemSet unique_together, Assignment score/completion fraction validation, Submission uniqueness constraint, JSON answer storage, submitted_at lifecycle

### API tests (`api/tests/`)
- `test_assignment_api.py`: Permission enforcement (students cannot create assignments, teachers cannot create submissions), role-based visibility (students only see enrolled assignments), duplicate submission prevention, submission update workflow

---

## Migration Notes

Migration `0002_question_questiontag_subjectroom_questionsubpart_and_more`:
- Creates all 7 new tables
- Adds indexes on: `(chapter, is_active)`, `(school, standard, subject)`, `(classroom, is_active)`, `(subject_room, due_at)`, `(student, submitted_at)`
- Adds unique_together on: `(question, index)` for subparts, `(classroom, subject)` for subject rooms, `(school, standard, subject, chapter, number)` for problem sets, `(assignment, student)` for submissions
- Safe to run against existing data (all new tables)

---

## Legacy Reference

- `core/models.py` → Question, QuestionSubpart, QuestionTag, AssignmentQuestionsList, Assignment, SubjectRoom, Submission
- `edge/models.py` → Tick, Proficiency (analytics — builds on Submission, next task)

---

## What This Unblocks

1. **Analytics engine** (`edge` app) — `Tick` and `Proficiency` models depend on `Submission`
2. **Student dashboard** — needs `Assignment` list + `Submission` state
3. **Teacher dashboard** — needs `SubjectRoom` + `Assignment` creation
4. **Grading pipeline** (Celery) — grades `Submission.answers` when `submitted_at` is set
5. **Cabinet integration** — `CabinetClient` serves question content for `Question` + `QuestionSubpart`

---

## Next Steps

1. **Analytics engine** — `Tick` model (per-subpart attempt record) + `Proficiency` model with score `(0.7 * rate) + (0.3 * percentile)`, improved with decay and spaced repetition weight
2. **Frontend — Student dashboard** — Assignment list, question rendering (MathJax), answer submission UI
3. **Frontend — Teacher dashboard** — Create assignment flow, SubjectRoom management
4. **Grading Celery task** — Auto-grade when `submitted_at` is set
