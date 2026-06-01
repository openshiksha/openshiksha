# AI Assignment Draft Builder

**Category:** Teacher AI Assistant (#7)
**Status:** Shipped
**Date:** 2026-05-31
**App:** `backend/openshiksha/apps/ai/`

## Problem it solves

Creating an assignment by hand is two tedious steps for a teacher: first work out
*which chapters the class is actually weakest on*, then hunt the question bank for
items at the right difficulty that the class hasn't already seen. Teachers rarely
have time to do both well, so practice often isn't targeted where it's needed.

The Assignment Draft Builder does both automatically and hands the teacher a
**reviewable draft** — nothing is assigned to students until the teacher approves
it. It closes the remaining gap in the Teacher AI Assistant initiative (weekly
class reports and class misconception insights already shipped).

## How it works (technical)

1. **Rank class weakness** — `analytics.rank_weak_chapters_for_room()` aggregates
   every `Tick` in the SubjectRoom over the last 45 days by chapter and returns the
   lowest-scoring chapters first. Chapters below the 50% struggle threshold are
   preferred; if the class isn't struggling anywhere it still returns the weakest
   chapters so the teacher always gets something usable.

2. **Select questions** — `analytics.build_assignment_draft()` spreads the
   requested number of questions across those chapters (weakest chapter gets the
   extra slots), picking active questions nearest the requested difficulty and
   **skipping any question assigned to the room in the last 60 days**. A second
   pass backfills shortfalls from the other weak chapters. This stage is pure,
   deterministic, and offline-safe — no LLM involved.

3. **Generate a rationale** — `llm_client.generate_draft_rationale()` writes a
   short plain-language note explaining which weaknesses the draft targets, via the
   standard provider cascade (Claude → Gemma → Ollama → deterministic stub). The
   stub guarantees a usable note when no API key is configured.

4. **Persist as a draft** — the `build_assignment_draft` Celery task upserts an
   `AssignmentDraft` row (`status=ready`), storing the structured selection,
   targeted chapters, rationale, and token usage. If nothing could be built (no
   recent data, or no fresh questions in the bank) it flips to `status=failed`
   with a human-readable reason.

5. **Approve into a real assignment** — on the `approve` action the draft is
   materialised into a `ProblemSet` + `Assignment` using the exact same core
   models the manual flow uses, so downstream grading and analytics are unchanged.
   The ProblemSet is anchored on the weakest targeted chapter.

The structured `selected_questions` snapshot keeps the draft fully renderable even
when the LLM provider is down, and makes the AI's choices auditable — each item
records which class weakness it targets.

## Models / APIs created

**Model:** `AssignmentDraft` (`ai_assignment_drafts`)
- `subject_room`, `requested_by`, `status` (pending/ready/approved/dismissed/failed)
- `title`, `rationale_text`, `target_difficulty`, `requested_size`
- `target_chapters` (JSON), `selected_questions` (JSON), `estimated_minutes`
- `approved_problem_set`, `approved_assignment` (set on approval)
- `model_used`, `input_tokens`, `output_tokens`, `error_detail`
- Properties: `question_count`, `is_actionable`

**Endpoints** (teacher-only, under `/api/v1/ai/assignment-drafts/`):
- `GET /` — list drafts for the teacher's rooms (`?subject_room=`, `?status=` filters)
- `GET /{id}/` — retrieve a draft
- `POST /generate/` — create a `pending` draft and queue assembly
  (`{subject_room_id, size?, target_difficulty?}`); poll until `status=ready`
- `POST /{id}/approve/` — materialise into a real Assignment (`{due_at, title?}`)
- `POST /{id}/dismiss/` — discard a draft

**Supporting code:**
- `analytics.rank_weak_chapters_for_room`, `build_assignment_draft` (+ helpers)
- `llm_client.generate_draft_rationale`
- `tasks.build_assignment_draft`
- Serializers: `AssignmentDraftSerializer`, `GenerateAssignmentDraftSerializer`,
  `ApproveAssignmentDraftSerializer`
- Admin: `AssignmentDraftAdmin`
- Migration: `0009_assignmentdraft`

## User impact

**Teachers** get a one-click, data-driven starting point for every assignment:
the system surfaces exactly where the class is weak and assembles a targeted,
non-repetitive question set, then steps back so the teacher reviews and adjusts
before anything reaches students. It removes the busywork while keeping the
teacher fully in control.

**Students** receive practice aimed at their class's real weak spots instead of
generic problem sets, and won't be re-served questions they just saw.

## Future enhancements

- Frontend panel in the teacher dashboard (V2 "Chalk & Unlock" design system) to
  request, preview, edit, and approve drafts.
- Per-student (remedial) drafts using `LearningGap` rather than class-level data.
- Mix in AI-generated questions (LLM Question Generation) when the bank is thin.
- Let the teacher swap individual questions before approving.
- Difficulty laddering (easy → hard) within a single draft.

## Dependencies

- Core: `SubjectRoom`, `Question`, `ProblemSet`, `Assignment`, `Chapter`
- Edge: `Tick` (source of class performance signal)
- Existing AI infra: `llm_client` provider cascade, Celery task conventions
- No new third-party packages.
