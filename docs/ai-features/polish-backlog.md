# AI Surfaces — Polish Backlog

Running log of polish work on the existing AI surfaces (no new features). Each
entry is one focused run against the 8-point polished checklist (error/degradation
states, loading states, copy/tone, empty states, placement, V2 design, provider
cascade transparency, test coverage).

---

## 2026-06-05 — AI question generation: stub mode no longer shown as real drafts

**Surface:** AI question generation (teacher `CreateQuestionPage`).

**Gap (checklist #1 & #7 — degradation / provider cascade transparency):**
When no LLM provider key was configured, the backend cascade fell back to a
deterministic stub that produced drafts like `"Sample mcq question 1 (AI provider
unavailable)"`. The endpoint returned these as ordinary drafts with no signal,
so the teacher saw placeholder text rendered as genuine, clickable "Use this"
draft cards — and could pre-fill the form with garbage content.

**Fix:**
- `llm_client.generate_questions()` now returns `{"questions": [...],
  "ai_available": bool}`; `ai_available` is `False` only when the stub path ran.
- `GenerateQuestionsViewSet` forwards `ai_available` and withholds the stub
  drafts (`questions: []`) when AI is unavailable.
- Frontend `useGenerateQuestions` response type gains `ai_available`;
  `AIGenerationPanel` shows a warm amber "AI unavailable right now, try again
  later" notice instead of rendering stub drafts.
- Added backend test `test_generate_questions_stub_mode_returns_no_drafts` for
  the fallback path (checklist #8).

**Verify:** Run the teacher question creator with no `ANTHROPIC_API_KEY` /
`GOOGLE_AI_API_KEY` / Ollama → "Generate" shows the amber unavailable notice,
not fake drafts. With a key set, drafts render as before.

---

## Remaining gaps (audit notes — not yet addressed)

- **Natural language explanations** — backend `SubpartExplanationViewSet` is
  registered (`/ai/explanations/`) but is **not consumed anywhere in
  `frontend_modern`**. The post-grading student feedback surface appears to be
  unwired in the V2 app. Needs UX placement work (inline after feedback) — sizeable,
  flag before treating as polish vs. feature.
- **Other generation surfaces** (weekly reports, parent summaries, class summary,
  interventions) use the same stub-cascade pattern. Audit each for whether the
  stub model leaks to the UI as if it were real content, mirroring the
  question-generation fix above. `generate_class_summary` returns
  `{"text", "model"}` — check the view/UI actually distinguish `model == "stub"`.
- **Hint system** — solid: loading ("Thinking of a good hint…"), error, and
  exhausted states all present. Low priority.
