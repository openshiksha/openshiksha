# Intelligent Hint System

**Category:** 3 — Intelligent Hint System
**Date:** 2026-05-28
**Branch:** `ai/2026-05-28-intelligent-hint-system`

## Problem it solves

When a student is stuck on a question, the legacy platform gave them two options:
guess, or give up. There was at most a single static `hint_text` per subpart, and
nothing that explained *why* a wrong answer was wrong.

This feature adds two complementary capabilities:

1. **Progressive hints** — an ordered chain of hints (gentle nudge → more concrete
   → near-method) that guides a student to work out the answer *themselves*
   without ever revealing it.
2. **Misconception detection** — after a wrong answer, a structured diagnosis of
   the underlying faulty reasoning (a short label + plain-language explanation +
   a remediation tip), so the student learns from the mistake and teachers can
   see misconceptions shared across a class.

## How it works (technical)

### LLM layer (`apps/ai/llm_client.py`)
Two new functions reuse the existing provider cascade
(Anthropic Claude → Google Gemma → Ollama → deterministic stub):

- `generate_hint_sequence(question_text, options, correct_answer, grade_level,
  num_hints, static_hint)` → `{hints: [{level, text}], model, input_tokens,
  output_tokens}`. The prompt explicitly forbids revealing the answer. The stub
  falls back to the subpart's static `hint_text` (if present) or generic study
  prompts, so the panel is always useful even with no LLM provider configured.
- `diagnose_misconception(question_text, options, student_answer, correct_answer,
  grade_level)` → `{misconception_label, diagnosis, remediation, model, tokens}`.

Both use Anthropic tool-calling for structured output, with JSON-parsing
fallbacks for Gemma/Ollama, and a `_parse_hints` normaliser that renumbers levels
and truncates to the requested count.

### Models (`apps/ai/models.py`, migration `0006`)
- **`HintSequence`** — `OneToOne` to `QuestionSubpart`. Hints are
  student-agnostic and **cached once per subpart**, so the LLM is called once per
  question rather than once per student. Stores `hints` (JSON), grade level, and
  model/token metadata.
- **`StudentMisconception`** — per `(student, subpart, submission)` diagnosis of a
  wrong answer. Upserted (idempotent); only created for incorrect answers.

### API (`apps/ai/views.py`, `urls.py`)
- `GET  /api/v1/ai/hints/?subpart=<id>` — list cached hint sequences (students).
- `POST /api/v1/ai/hints/generate/` — **synchronous** generate-or-fetch. Returns
  the cached sequence if one exists (200), otherwise generates, caches, and
  returns it (201). The response never includes the correct answer.
- `GET  /api/v1/ai/misconceptions/` — students see their own; teachers see
  diagnoses for students in subject rooms they teach.
- `POST /api/v1/ai/misconceptions/diagnose/` — queues async diagnosis via Celery
  (`diagnose_misconception_for_subpart`).

Hint generation is synchronous (students need hints *while* solving and caching
keeps it cheap); misconception diagnosis is async (it happens after grading and
isn't blocking).

### Frontend (`frontend_modern/`)
- `useHints` hook (`features/student/useHints.ts`) — React Query mutation.
- `AIHintPanel` in `QuestionCard.tsx` — replaces the old single static-hint
  reveal. A "💡 Get a hint" button fetches the sequence, then reveals one hint at
  a time via "Show next hint (n/N)", so the student is nudged gradually.

## User impact

- **Students** get unstuck without being handed the answer, building real
  problem-solving skill; after a mistake they understand *why* it was wrong.
- **Teachers** can (via the misconceptions endpoint) see recurring misconceptions
  across a class — a signal for what to reteach.

## Tests
`apps/ai/tests/test_hint_system.py` (24 tests): models, llm_client stub/cascade/
parsing/no-answer-leak, the Celery diagnosis task (idempotent), and the API
(synchronous caching, answer not exposed, role permissions, student isolation,
teacher class visibility). Full `ai` suite (194 tests) passes.

## Future enhancements
- Track per-student hint usage to flag over-reliance and adjust proficiency
  scoring.
- Aggregate `StudentMisconception` into a teacher dashboard ("8 students share
  this misconception").
- Socratic mode: a back-and-forth dialogue instead of a fixed hint chain.
- Multi-language hints (reuse the `en`/`hi` calibration from explanations).

## Dependencies
- Existing `apps/ai` LLM cascade and `QuestionSubpart` (incl. `hint_text`).
- No new third-party packages.
