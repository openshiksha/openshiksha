# 2026-04-03 — Teacher Assignment Detail, Problem Set Builder, Croupier Phase 1

## Summary

Three features shipped today to complete the teacher content creation loop and add the first anti-cheating layer.

1. **Teacher Assignment Detail** — `/teacher/assignments/:id` now works. Previously every assignment row in the TeacherDashboard navigated to a 404. Now shows a per-student submission table with name, timestamp, score, and status.

2. **Problem Set Builder** — `/teacher/problem-sets/new` closes the gap in `Create Question → ??? → Assign`. Teachers can now group their authored questions into an assignable Problem Set without touching Django admin.

3. **Croupier Phase 1** — Deterministic MCQ option shuffling. Different students see MCQ options in different orders, seeded per `(student_id, subpart_id)`. The grader reverses the shuffle automatically so scoring is unaffected.

---

## Classification

| Feature | Type | Notes |
|---------|------|-------|
| Teacher assignment detail | **New** | Legacy had no teacher-facing per-assignment page (only Django admin) |
| Problem Set builder | **New** | Legacy created problem sets via admin only; teachers had no UI |
| Croupier Phase 1 | **Port + Improve** | Legacy Croupier used Cabinet HTTP service; now pure Python, in-process |

---

## Legacy Reference

### Teacher assignment detail (legacy had none)
The original Django 1.11 platform had no teacher-facing assignment detail page. Teachers could only inspect submissions through the Django admin interface. This is a net-new feature.

### Problem Set builder
Legacy problem sets were created via `AssignmentQuestionsList` in Django admin. Teachers couldn't manage their own question banks — the platform admin had to do it. This removes that dependency.

### Croupier (port + improvement)
The legacy `croupier/` module fetched question content from Cabinet, substituted variable values (seeded by user ID), and shuffled MCQ options. It ran server-side on every page load via an HTTP call to Cabinet.

**What changed:**
- No Cabinet dependency — pure Python, in-process
- Seed is `SHA-256(student_id:subpart_id)` — cryptographically uniform, no modular bias from small seeds
- Re-keys options by display position after shuffle so students always see A/B/C/D labels
- Grader calls `get_original_key()` to reverse-map submitted keys — no new DB fields needed

---

## Technical Details

### Backend

**`apps/api/croupier.py`** (new)
- `shuffle_options_for_student(options, student_id, subpart_id)` — deterministic shuffle, re-keys by position
- `get_original_key(student_id, subpart_id, submitted_key, original_options)` — reverse-maps position key → original storage key
- Seed: `int(SHA-256(f"{student_id}:{subpart_id}"), 16) % 2^32`

**`apps/api/serializers/core.py`**
- `SubmissionSerializer` — added `student_name = SerializerMethodField()` using `get_full_name() or username`
- `QuestionSubpartStudentSerializer.to_representation()` — applies shuffle when `request.user` is authenticated and `options` is non-null
- `ProblemSetWriteSerializer` — new; accepts `question_ids` (M2M), validates at least one question

**`apps/api/views/core.py`**
- `ProblemSetViewSet` promoted from `ReadOnlyModelViewSet` to `ModelViewSet`; teacher-only for write actions
- `perform_create` sets `school` and `created_by` from request user

**`apps/core/tasks.py`**
- `grade_submission` now passes `student_id`, `subpart_id`, `original_options` to `_grade_subpart`
- `_grade_subpart` calls `get_original_key()` for MCQ/multi_select before comparing to `correct_answer`

### Frontend

**New files:**
- `TeacherAssignmentDetailPage.tsx` — submission table with score, time, status badges; fetches metadata + submissions in parallel
- `useTeacherAssignmentDetail.ts` — two React Query hooks: assignment metadata + `/submissions/` endpoint
- `CreateProblemSetPage.tsx` — title/subject/chapter/time inputs + scrollable question picker with checkbox multi-select; on success offers "Assign it now" CTA
- `useCreateProblemSet.ts` — `POST /api/problem-sets/` mutation
- `useQuestionList.ts` — `GET /api/questions/` with subject/chapter/standard filters

**Modified:**
- `App.tsx` — added `/teacher/assignments/:id` and `/teacher/problem-sets/new` routes
- `TeacherDashboard.tsx` — added "+ Problem Set" button alongside existing "+ New Question" and "+ New Assignment"

---

## Tests Written

### Backend
- `test_croupier.py` — 13 pure-Python tests (no DB):
  - Determinism: same `(student_id, subpart_id)` → same shuffle
  - Anti-cheat: different students → different orders
  - All original option texts preserved after shuffle
  - Keys re-assigned by position (A, B, C, D)
  - `get_original_key()` round-trips correctly for every position
  - Correct answer survives full flow: shuffle → student submits → reverse-map → grade correctly
  - Wrong answer still scores zero
  - Non-MCQ question types unaffected

- `test_problemset_api.py` — 7 DB tests (require Postgres/Docker):
  - Teacher can create problem set via `POST /api/problem-sets/`
  - Created set has correct questions in M2M
  - Student gets 403 on create
  - Empty `question_ids` returns 400
  - Newly created set appears in list endpoint
  - `GET /api/assignments/{id}/submissions/` returns `student_name`
  - Student cannot access submissions endpoint (403)

### Frontend
- TypeScript: 0 errors
- ESLint: 0 warnings

---

## Migration Notes

No model changes — no migrations needed.

`ProblemSet.questions` M2M and `ProblemSet.created_by` already existed. `SubmissionSerializer.student_name` is a read-only computed field.

---

## Next Steps

- **Croupier Phase 2**: Variable substitution — add `variable_constraints: JSONField` to `QuestionSubpart`, generate numeric values seeded by `(student_id, question_id)`, substitute `{{x}}` tokens in `question_text` and option texts
- **Teacher analytics: question-level mistakes** — `SubjectRoomQuestionMistake` data exists from grading; surface it on the teacher assignment detail page as a "Hardest Questions" section
- **LearningGap computation** — AI models (`LearningGap`, `ClassInsight`) exist but no Celery task populates them yet
- **Spaced repetition UI** — SM-2 engine is complete in `apps/ai/`; nothing surfaces it to students
