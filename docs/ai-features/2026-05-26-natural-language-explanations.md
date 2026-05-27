# Natural Language Explanations

**Category:** AI Feature #6
**Date:** 2026-05-26
**PR:** https://github.com/openshiksha/openshiksha/pull/92

## Problem it solves

Students currently receive only a score after grading — they know they got something wrong, but not *why*. This feature adds a short, encouraging plain-language explanation for every question subpart, telling the student what the correct reasoning is and reinforcing understanding rather than just marking.

## How it works

### Provider cascade

The `llm_client.py` module tries providers in order, falling back gracefully:

1. **Anthropic Claude** (`ANTHROPIC_API_KEY`) — highest quality, paid
2. **Google Gemma 4 via AI Studio** (`GOOGLE_AI_API_KEY`) — free tier, 1M tokens/month
3. **Ollama on-device Gemma** (`OLLAMA_BASE_URL` or `localhost:11434`) — fully local, zero cost
4. **Stub** — plain text, no LLM call, safe for dev/test

### Grade calibration

Prompts are tiered by the student's grade level:
- **Std 1–6 (primary):** Very simple words, short sentences, real-life analogies
- **Std 7–9 (middle):** Clear language, explains the concept and the mistake
- **Std 10–12 (senior):** Subject-specific terms allowed, concise

### Language support

Currently English (`en`) and Hindi (`hi`, Devanagari script). Language is requested via the `generate` endpoint.

### Integration with grading pipeline

After `grade_submission` completes, it enqueues `generate_explanations_for_submission`. The task:
1. Loads all `Tick` records for the submission
2. For each tick, calls the LLM cascade with the question text, student answer, correct answer, grade level
3. Upserts a `SubpartExplanation` record (idempotent — safe to re-run)

Students can also request on-demand explanations for SRS drill answers via `POST /api/v1/ai/explanations/generate/`.

## Models created

### `SubpartExplanation`
- `student`, `question_subpart`, `submission` — unique together
- `student_answer` — what they submitted
- `is_correct` — grading outcome
- `explanation_text` — AI-generated explanation (2–4 sentences)
- `language`, `grade_level` — context used for generation
- `model_used`, `input_tokens`, `output_tokens` — cost tracking

## APIs created

| Endpoint | Method | Access | Description |
|---|---|---|---|
| `/api/v1/ai/explanations/` | GET | Student | List own explanations (`?submission=`, `?subpart=`) |
| `/api/v1/ai/explanations/{id}/` | GET | Student | Single explanation |
| `/api/v1/ai/explanations/generate/` | POST | Student | On-demand for SRS drill |

## User impact

- **Students:** After submitting an assignment, they can review *why* each answer was right or wrong — without waiting for a teacher. Makes the platform more self-sufficient.
- **Teachers:** No action required — explanations appear automatically. Teachers save time on explaining individual mistakes.
- **Parents:** Students who understand their mistakes self-correct faster — measurable improvement in subsequent assignment scores.

## Future enhancements

- Show explanations inline in the assignment review UI (frontend component)
- Multi-language expansion (Tamil, Telugu, Marathi)
- Teacher can "approve" or "edit" an explanation before it's shown
- Track whether students who read explanations improve on similar questions (feedback loop)
- Use misconception patterns to improve future prompts (connect to Intelligent Hint System)

## Dependencies

- `anthropic==0.52.0` — Claude API SDK
- `google-genai==1.16.0` — Google AI Studio / Gemma 4 SDK
- `httpx` (already in requirements) — used for Ollama health check and HTTP calls
