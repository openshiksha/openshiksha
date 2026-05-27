# 2026-05-26 — LLM Question Generation (P0)

## Summary

Teachers can now generate question drafts using Claude AI directly from the question
authoring interface. Drafts are editable before saving. Existing questions can now be
edited via the question bank. Problem sets have an "add question" action to add
questions from the bank without re-creating them.

## Classification

**New** (LLM generation) + **Improve** (edit existing questions, add-to-problem-set)

## Legacy files referenced

- `sphinx/views.py` — legacy question authoring: board/school/chapter structure, submit flow
- `cabinet/cabinet_api.py` — image/JSON storage (skipped; modern uses DB)

## What changed from legacy

- Legacy sphinx had a pure Django-template authoring UI — no AI assistance
- Modern adds Claude AI (tool_use for structured JSON output) with provider cascade:
  Anthropic Claude → Google Gemma 4 → Ollama → stub
- Question editing was missing entirely (legacy had cabinet JSON files editable via CLI);
  modern adds `PATCH /api/v1/questions/<id>/` scoped to `created_by == request.user`

## Technical details

### Backend

**`apps/ai/llm_client.py`** — new `generate_questions()` function:
- Uses Anthropic tool_use (`save_questions` tool) for structured JSON output
- Falls back to Google Gemma 4 / Ollama (JSON prompt + parse) / stub
- Returns `list[dict]` with `question_text`, `options`, `correct_answer`,
  `variable_constraints`, `suggested_tags`

**`apps/ai/views.py`** — new `GenerateQuestionsViewSet.create()`:
- `POST /api/v1/ai/generate-questions/` — teacher-only
- Validates request with `GenerateQuestionsRequestSerializer`
- Fetches Chapter + related subject/standard for prompt context
- Returns `GeneratedQuestionDraftSerializer` output (validated, not saved)
- 503 on LLM failure; 403 for non-teachers; 404 for bad chapter_id

**`apps/api/views/core.py`** — `ProblemSetViewSet.add_question()`:
- `POST /api/v1/problem-sets/<id>/add-question/`
- Teacher must be `created_by` of the problem set
- Body: `{"question_id": <int>}`
- Idempotent (M2M add is a no-op if already present)

### Frontend

- **`useGenerateQuestions.ts`** — mutation hook for `POST /ai/generate-questions/`
- **`useAddQuestionToProblemSet.ts`** — mutation hook for `POST /problem-sets/<id>/add-question/`
- **`useQuestion.ts`** — single-question fetch by ID (for edit mode)
- **`useUpdateQuestion.ts`** — PATCH mutation for editing a question
- **`CreateQuestionPage.tsx`** — fully reworked:
  - Collapsible "Generate with AI" panel (indigo-50, ✨ sparkle icon, chevron toggle)
  - AI panel: topic textarea, type/difficulty/count selectors, Generate button, skeleton loaders
  - Draft cards with amber "Draft" badge, "Use this" pre-fill button
  - Retry button on AI generation failure
  - Edit mode: `editMode` prop + `useParams({ id })`, pre-fills form from existing question,
    calls PATCH instead of POST
  - Route `/teacher/questions/:id/edit` added to `App.tsx`
- **`QuestionBankPage.tsx`** — new action buttons on each card:
  - "+ Add to problem set" → opens `AddToProblemSetModal`
  - "Edit" → navigates to `/teacher/questions/:id/edit`
  - `AddToProblemSetModal`: radio list of teacher's problem sets for that subject,
    success state with "Done" button, error inline

## Tests written

- `apps/ai/tests/test_generate_questions.py` — 6 tests:
  success, forbidden for students, invalid chapter, invalid count, LLM failure → 503,
  unauthenticated → 401
- `apps/api/tests/test_problemset_api.py` — 6 new tests in `TestAddQuestionToProblemSet`:
  teacher can add, idempotent add, student forbidden, other teacher forbidden,
  missing question_id → 400, nonexistent question → 404

All 19 new tests pass.

## Migration notes

No migrations needed — no model changes.

## Next steps

- P4 — School admin frontend (list classrooms, enroll students)
- P6 — Lodge video content (Video model, VideosPanel)
- P7 — Concierge enquiry form
- P8 — Cabinet question import (679 real questions from openshiksha-cabinet)
