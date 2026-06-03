# Intervention Suggestions (Teacher AI Assistant)

**Category:** #7 Teacher AI Assistant — "Suggest intervention strategies for
struggling students"
**Status:** Shipped
**Date:** 2026-06-02

## Problem it solves

OpenShiksha already tells a teacher *what* is wrong — `LearningGap` flags each
student's weak chapters, `StudentMisconception` captures *why* answers are wrong,
and `ClassInsight` aggregates struggle at the class level. None of those answer
the teacher's actual next question: **"OK — what do I do about it?"**

This feature closes that loop. For each struggling student in a SubjectRoom it
bundles the evidence the rest of the AI suite already produces and asks an LLM to
write a short, concrete intervention plan the teacher can act on this week —
worst-affected students first.

## How it works

1. **Evidence join (no recompute).**
   `analytics.compute_interventions_for_subject_room` reads the already-persisted
   open `LearningGap` rows for the room and each affected student's
   `StudentMisconception` labels. It groups gaps per student and builds a snapshot:
   weakest chapters (worst-first), recurring misconception labels with counts,
   mean gap score, gap count, worst severity, and a derived priority.

2. **Priority.** `InterventionSuggestion.priority_for(severity, gap_count)` maps
   severity + breadth to a 1–5 urgency score deterministically (severe → 4,
   moderate → 3, mild → 2; each extra gap nudges up, capped at 5). The teacher's
   list sorts by priority desc, then average score asc.

3. **Narrative.** `llm_client.generate_intervention_plan` runs the standard
   provider cascade (Claude tool-free text → Gemma → Ollama → deterministic
   stub). The stub composes a usable plan from the snapshot, so the card always
   renders even with **no LLM provider configured**.

4. **Persistence + lifecycle.** `tasks.generate_interventions_for_subject_room`
   upserts one `InterventionSuggestion` per (room, student). A teacher's
   acknowledge/dismiss/resolve decision is preserved across refreshes; students
   whose gaps have closed are **auto-resolved** so the list self-cleans.

## Models / APIs created

### Model — `InterventionSuggestion` (`ai_intervention_suggestions`)
`subject_room`, `student` (unique together), `status`
(open/acknowledged/dismissed/resolved), `priority` (1–5), `severity`,
`strategy_text`, plus the auditable snapshot (`avg_score`, `gap_count`,
`focus_chapters`, `misconception_labels`) and cost fields (`model_used`,
`input_tokens`, `output_tokens`). Migration `ai/0011`.

### API (teacher-only, `/api/v1/ai/interventions/`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/ai/interventions/` | Suggestions for the teacher's rooms (`?subject_room=`, `?status=`) |
| GET | `/ai/interventions/{id}/` | Single suggestion |
| POST | `/ai/interventions/generate/` | Queue generation `{subject_room_id}` |
| POST | `/ai/interventions/{id}/set-status/` | `{status: acknowledged\|dismissed\|resolved}` |

A teacher only ever sees and acts on suggestions for rooms they teach;
acknowledging stamps `acknowledged_by` / `acknowledged_at`.

### Frontend
- `useInterventions.ts` — React Query hook + `generate` / `set-status` mutations.
- `InterventionsPanel.tsx` — collapsible per-room panel on the Teacher Dashboard,
  built on the **V2 "Chalk & Unlock"** primitives (`Card`, `Badge`, `Button`,
  brand orange, Fraunces headings, paper/ink surfaces). Each card shows the
  student, the AI strategy, weak-chapter chips, the recurring misconception, and
  Dismiss / "Mark as planned" / Resolve actions.

## User impact

**Teachers** get a prioritised, plain-language action list — "start with Asha on
Long Division, re-teach with a worked example addressing the
'adds-numerators-and-denominators' misconception, check with an exit question
next week" — instead of cross-referencing gap tables and misconception clusters
themselves. The human stays fully in control: AI suggests, the teacher decides.

## How to verify

```bash
# Backend
cd backend
./venv/Scripts/python.exe -m pytest openshiksha/apps/ai/tests/test_interventions.py --no-cov -q
./venv/Scripts/python.exe manage.py check

# Frontend
cd frontend_modern
npx vitest run src/features/teacher/InterventionsPanel.test.tsx
npx tsc --noEmit
```

Then: log in as a teacher, expand **Intervention Suggestions** on a class with
known learning gaps, click **Generate**, and act on a card.

## Future enhancements

- Surface a class-wide intervention digest (group students who share a
  misconception into one re-teach plan, linking `ClassMisconceptionCluster`).
- One-click "create targeted practice" that hands the focus chapters to the
  existing `AssignmentDraft` generator.
- Email/notification nudge when a new high-priority intervention appears.
- Track outcome: did the student recover after the teacher acted? Feed back into
  priority.

## Dependencies

Builds entirely on existing derived data — `LearningGap`,
`StudentMisconception`, the shared `llm_client` provider cascade, and the V2
`shared/ui` primitives. No new third-party dependencies. Self-contained: works
with zero LLM keys via the deterministic stub.
