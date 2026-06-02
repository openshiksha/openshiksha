# AI-Assisted Open-Ended Response Grading

**Category:** Teacher AI Assistant (#7)
**Status:** Shipped (backend)
**Date:** 2026-06-01
**App:** `backend/openshiksha/apps/ai/`

## Problem it solves

OpenShiksha grades MCQ, fill-in-the-blank, numeric, matching and multi-select
answers automatically — they all reduce to a string or float comparison. But a
**free-text answer cannot grade itself**: a student can be completely right while
phrasing things nothing like any stored key. Until now there was no way to author
open-ended ("short answer") questions and have them assessed, so teachers either
avoided them or graded every response by hand.

This feature adds **AI-assisted** grading for free-text answers. The LLM proposes
a score, plain-language feedback and an optional per-criterion breakdown; the
teacher reviews and accepts or overrides it. The human always has the final say —
this is a time-saver, not an auto-grader that locks the teacher out.

It closes the last major gap in the Teacher AI Assistant initiative (weekly class
reports, class misconception insights, and the assignment draft builder already
shipped).

## How it works (technical)

1. **New question type** — `QuestionType.SHORT_ANSWER` lets a question be authored
   as open-ended. The core grading pipeline already returns `0.0` for unknown
   types, so short-answer subparts never get a misleading auto-mark; this feature
   supplies the real assessment instead.

2. **Rubric** — `OpenResponseRubric` (one per subpart) holds the `max_marks`, an
   ideal `model_answer`, and an optional analytic `criteria` list
   (`[{"label", "description", "marks"}]`). Teachers author it via CRUD. The rubric
   is optional: without it the grader falls back to the model answer only, or a
   keyword-overlap heuristic.

3. **Grade suggestion** — `llm_client.grade_open_response()` builds a marking
   prompt (question + model answer + rubric + student response, grade-calibrated)
   and runs the standard provider cascade:
   **Claude (tool-use) → Gemma / Ollama (JSON) → deterministic keyword-overlap
   stub**. It returns `{score, feedback, confidence, criterion_scores}`. Scores are
   clamped to `[0, max_marks]` and confidence to `[0, 1]`, so a misbehaving model
   can't write an out-of-range mark. The stub awards marks by the fraction of
   model-answer keywords present in the response and reports low confidence so the
   teacher knows to look closely.

4. **Persist + review** — `OpenResponseGrade` stores the student's `response_text`,
   the AI suggestion, and the teacher's review fields. The `grade_open_response`
   Celery task fills in the suggestion and flips the row `pending → ai_graded`
   (or `failed` with a reason). The teacher's `review` action writes `final_score`
   and flips it to `reviewed`. `effective_score` resolves to the teacher's final
   mark once reviewed, otherwise the AI's suggestion, so dashboards always have a
   number.

The whole feature lives in `apps/ai/` and is independent of the core submission
pipeline — a response can be entered by the teacher or fed in from any future
submission integration. `subject_room` scopes every row to the teacher who teaches
it; a teacher never sees or acts on another room's grades.

## Models / APIs created

**Models** (`apps/ai/models.py`, migration `0010`; core migration `0015` adds the
`SHORT_ANSWER` choice):
- `OpenResponseRubric` — subpart rubric: `max_marks`, `model_answer`, `criteria`.
- `OpenResponseGrade` — a response + AI suggestion + teacher review.
  `OpenResponseGradeStatus`: `pending → ai_graded → reviewed` (or `failed`).

**API** (teacher-only, all under `/api/v1/ai/`):
- `GET/POST/PATCH/DELETE open-rubrics/` — manage rubrics (`?subpart=<id>`).
- `GET open-grades/` — list, filterable by `?subject_room=`, `?status=`,
  `?student=`.
- `POST open-grades/submit/` — record a response and queue AI grading
  (`{subpart_id, student_id, subject_room_id, response_text, assignment_id?}`).
- `POST open-grades/{id}/regrade/` — re-run the grader (blocked once reviewed).
- `POST open-grades/{id}/review/` — finalise (`{final_score, teacher_comment?}`),
  rejecting a `final_score` above `max_marks`.

**LLM client:** `grade_open_response()` + `_build_open_grade_prompt`,
`_stub_open_grade`, `_shape_open_grade` helpers and a `save_grade` tool schema.

**Celery task:** `grade_open_response(grade_id)` — idempotent, marks `failed` on
error rather than leaving a row stuck in `pending`.

**Admin:** `OpenResponseRubricAdmin`, `OpenResponseGradeAdmin`.

## User impact

- **Teachers** can finally use short-answer questions without hand-grading every
  response. The AI does the first pass; the teacher skims, accepts or adjusts, and
  moves on. Low-confidence suggestions are flagged so attention goes where it's
  needed.
- **Students** get specific, encouraging written feedback on open-ended answers,
  not just a mark — and partial credit when they're partly right.

## Tests

`apps/ai/tests/test_open_response_grading.py` (20 tests): model properties; the
grading cascade (stub high/low overlap, score/confidence clamping, Anthropic
tool-use, Google JSON, prompt contents); the Celery task (success → `ai_graded`,
already-reviewed no-op, error → `failed`); and the API (rubric CRUD + permissions,
submit queues the task, room scoping, review sets/clamps the final score, regrade
requeue and its reviewed-row block, student forbidden). Full suite: 321 passing.

## How to verify

1. `python manage.py migrate` (applies ai `0010` + core `0015`).
2. As a teacher, `POST /api/v1/ai/open-rubrics/` with a `subpart` of a
   `SHORT_ANSWER` question, a `model_answer` and `max_marks`.
3. `POST /api/v1/ai/open-grades/submit/` with a student's `response_text`. With no
   LLM keys configured the stub grades it immediately; poll
   `GET /api/v1/ai/open-grades/{id}/` until `status=ai_graded`.
4. `POST /api/v1/ai/open-grades/{id}/review/` with `{"final_score": N}` to finalise.

## Future enhancements

- **Frontend** — a teacher review queue card (V2 "Chalk & Unlock" design system),
  mirroring how the Parent Intelligence Dashboard shipped backend-first (#107) then
  frontend (#109).
- **Student submission integration** — wire short-answer answers from the live
  assignment flow straight into `OpenResponseGrade` instead of teacher entry.
- **Write back to `Tick`** — once a grade is reviewed, feed `effective_score /
  max_marks` into the proficiency engine so open-ended work counts toward analytics.
- **Bulk grading** — one call to AI-grade every pending response in an assignment.

## Dependencies

None beyond the existing AI stack. Works fully offline via the deterministic stub;
uses `ANTHROPIC_API_KEY` / `GOOGLE_AI_API_KEY` / `OLLAMA_BASE_URL` when present.
