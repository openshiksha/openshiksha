# AI Tutor — Student-Facing Socratic Chat

**Category:** 3 — Intelligent Hint System (conversational extension) / student-facing AI tutor surface
**Date:** 2026-06-04
**Branch:** `ai/2026-06-04-ai-tutor-chat`

## Problem it solves

Until now the only student-facing AI help on a question was the **progressive
hint sequence** — a fixed, cached, student-agnostic chain of nudges. It's great
for "give me the next hint", but it can't respond to a student's *specific*
confusion ("I added the tops and bottoms, why is that wrong?"). A struggling
student often needs a back-and-forth, not a canned ladder.

This feature adds a **multi-turn AI Tutor chat**, anchored to the question the
student is working on. The tutor teaches Socratically: it asks one short leading
question at a time, builds on what the student already understands, and guides
them toward the answer **without ever stating it outright** — so it stays
available during live practice, unlike the worked solution which only unlocks
after grading. This is the "AI tutor surface" called out in the V2 roadmap
backlog, built on top of the existing hint + explanation LLM infrastructure.

## How it works (technical)

### LLM layer (`apps/ai/llm_client.py`)
A new `generate_tutor_reply(student_message, history, question_text, options,
correct_answer, grade_level, language)` reuses the established provider cascade
(Anthropic Claude → Google AI Studio → Ollama → deterministic stub), but for the
first time in **multi-turn chat** form:

- `_build_tutor_system_prompt(...)` produces a grade-calibrated Socratic system
  prompt. The anchored subpart's correct answer is injected **only as a
  guard-rail** ("For your reference only … NEVER state this answer outright") and
  is never returned to the student.
- New chat-shaped provider calls — `_call_anthropic_chat` (uses `system=` +
  user/assistant `messages`), `_call_google_chat` (uses `system_instruction` +
  role-mapped `Content` parts), and `_call_ollama_chat` (uses `/api/chat` with a
  `system` message) — replay the conversation history on every turn.
- `_stub_tutor_reply` returns a deterministic guiding question (different on the
  first turn vs. follow-ups) so the tutor is always usable with no LLM key, which
  is also what the test suite exercises.

### Models (`apps/ai/models.py`)
- **`TutorConversation`** — one chat session, owned by a student, optionally
  anchored to a `QuestionSubpart` (`on_delete=SET_NULL`, so deleting a question
  keeps the chat). Holds `grade_level`, `language`, `title` (derived from the
  first message), and timestamps.
- **`TutorMessage`** — one turn (`role` = student | tutor), ordered by
  `created_at`. Token/model fields populate only on tutor turns. Replaying these
  oldest-first is exactly the history sent to the LLM.

### API (`apps/ai/views.py`, `serializers.py`, `urls.py`)
`TutorConversationViewSet` (registered at `/api/v1/ai/tutor/`), **student-only**,
each student scoped to their own conversations:

- `POST /api/v1/ai/tutor/` — start a conversation `{subpart_id?, message?,
  grade_level?, language?}`. If `message` is supplied, the student turn is stored
  and the tutor reply generated synchronously.
- `POST /api/v1/ai/tutor/{id}/message/` — post a follow-up `{message}`; appends
  the student turn, generates + stores the tutor reply, returns the full
  conversation.
- `GET /api/v1/ai/tutor/` (+ `?subpart=<id>`) — the student's conversation
  history (lightweight, no message bodies).
- `GET /api/v1/ai/tutor/{id}/` — one conversation with all messages.

If the LLM cascade raises, the student's message is preserved and the endpoint
returns **503** with a friendly "try again" detail rather than losing the turn.
The correct answer is never present in any serialized payload.

### Frontend (`frontend_modern/`)
- `useTutor.ts` — `useStartTutor` / `useTutorMessage` React Query mutations.
- `AskTutorPanel.tsx` — a collapsed "🧑‍🏫 Ask the tutor" affordance under each
  subpart (next to the hint panel) that expands into a chat bubble UI. Built on
  the V2 "Chalk & Unlock" design system — brand-orange (`#FF6F00`) tutor
  accents (distinct from the amber hints), `input-brand` / `btn-brand`
  primitives, `RichContent` so tutor replies render math, and an `aria-live`
  message log. Only shown during practice (`!isSubmitted`).

## Models / APIs created

| Kind | Name |
|---|---|
| Model | `TutorConversation`, `TutorMessage` (+ `TutorMessageRole`) |
| Migration | `ai/migrations/0013_tutorconversation_tutormessage_and_more.py` |
| LLM fn | `generate_tutor_reply` (+ chat provider helpers, stub, system prompt) |
| API | `GET/POST /api/v1/ai/tutor/`, `POST /api/v1/ai/tutor/{id}/message/`, `GET /api/v1/ai/tutor/{id}/` |
| Serializers | `TutorConversation(List)Serializer`, `TutorMessageSerializer`, `StartTutorConversationSerializer`, `PostTutorMessageSerializer` |
| Admin | `TutorConversationAdmin` (+ message inline), `TutorMessageAdmin` |
| Frontend | `useTutor.ts`, `AskTutorPanel.tsx`, wired into `QuestionCard.tsx` |

## User impact

- **Students** get personal, conversational help that adapts to *their* specific
  confusion, available right where they practise — and it coaches them to the
  answer instead of handing it over, preserving the learning.
- **Teachers/parents** benefit indirectly: more students push through a hard
  question instead of guessing or quitting.

## Tests

`apps/ai/tests/test_tutor.py` (16 tests, all green): model ordering & SET_NULL,
stub vs. cascade replies, the answer guard-rail in the system prompt, history
role mapping, start-with/without-message, follow-up turns, empty-message
rejection, invalid subpart (404), owner scoping (list + retrieve), teacher
forbidden (403), and 503-on-LLM-failure with the message preserved. Full
`apps/ai` suite stays green (372 passed); frontend `tsc` + eslint clean.

## Future enhancements

- Streaming replies (SSE/WebSockets — Channels is already configured).
- A "tutor history" surface so students can revisit past conversations.
- Unanchored, topic-level tutoring ("explain photosynthesis") from the dashboard.
- Feed tutor transcripts into misconception detection for richer diagnoses.
- Per-student daily token budget / rate limiting.

## Dependencies

None new. Reuses the existing LLM provider cascade and SDKs already used by the
explanation/hint generators (`anthropic`, `google-genai`, `httpx`). Works with
no API key via the deterministic stub.
