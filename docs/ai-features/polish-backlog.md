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

## 2026-06-07 — Weekly class reports: AI-generated label + generation error state

**Surface:** Weekly class reports (teacher dashboard `WeeklyReportPanel`).

**Gaps (checklist #1 error states, #3 copy/tone, #7 provider transparency):**
1. The LLM-written `summary_text` was shown with **no indication it was
   AI-generated** — teachers had no signal the narrative came from a model.
2. When `model_used === 'stub'` (no LLM key — deterministic data-derived
   fallback), the stub text was presented identically to genuine AI output,
   violating provider-cascade transparency.
3. `handleGenerate` **silently swallowed errors**: if the generate POST failed,
   the panel just reverted to the empty "No weekly summary yet" state with no
   feedback, so a teacher couldn't tell the click had failed.

**Fix:**
- Added a small `Badge` on the report card: `✨ AI-generated` (brand tone) for a
  real LLM, or `Auto-summary` (neutral tone) plus an "AI was unavailable, so this
  was built directly from your class data" note when `model_used === 'stub'`.
- Added a friendly inline error message ("Couldn't generate the summary just now.
  Please try again in a moment.") on generation failure.
- New test file `WeeklyReportPanel.test.tsx` covers the AI label, the stub
  auto-summary path, and the generation-error path (checklist #8).

**Verify:** Expand "Weekly AI Summary" on the teacher dashboard. With a provider
key set the report shows the ✨ AI-generated badge; with no key the stub summary
shows the Auto-summary badge + note. Trigger a failing generate → red error line.

---

## 2026-06-07 — Parent intelligence dashboard: AI-generated label + stub note

**Surface:** Parent intelligence dashboard (`NarrativeCard`, parent
`ParentInsightsPage`).

**Gap (checklist #3 copy/tone, #7 provider transparency):**
The weekly parent summary narrative (`summary_text`) was shown with **no
indication it was AI-generated**, and when the provider cascade fell back to the
deterministic, data-derived stub (`model_used === 'stub'`) the stub text was
presented identically to genuine LLM output — exactly the inconsistency already
fixed on the teacher `WeeklyReportPanel`.

**Fix:**
- `NarrativeCard` now shows a `Badge` in the card header: `✨ AI-generated`
  (brand tone) for a real LLM, or `Auto-summary` (neutral tone) when
  `model_used === 'stub'`, plus a small "AI was unavailable, so this summary was
  built directly from your child's practice data" note under the narrative.
- `model_used` was already on the `ParentProgressSummary` type/serializer — no
  backend change needed.
- New test file `NarrativeCard.test.tsx` covers the AI-generated label and the
  stub auto-summary path (checklist #8).

**Verify:** Open the parent insights page. With a provider key set the weekly
summary card shows the ✨ AI-generated badge; with no key the stub summary shows
the Auto-summary badge + note.

---

## 2026-06-08 — Interventions: AI-generated label + generation error state

**Surface:** Intervention suggestions (teacher dashboard `InterventionsPanel`).

**Gaps (checklist #1 error states, #3 copy/tone, #7 provider transparency):**
1. Each per-student `strategy_text` is LLM-written but was shown with **no
   indication it was AI-generated** — the same inconsistency already fixed on
   `WeeklyReportPanel` and `NarrativeCard`. When the cascade fell back to the
   deterministic stub (`model_used === 'stub'`) the strategy was presented
   identically to genuine AI output.
2. `useGenerateInterventions` **silently swallowed errors**: a failing generate
   POST left the panel in its prior state with no feedback, so a teacher couldn't
   tell the click had failed.

**Fix:**
- Each `SuggestionCard` now shows a `Badge` above the strategy: `✨ AI-generated`
  (brand tone) for a real LLM, or `Auto-strategy` (neutral tone) plus an "AI was
  unavailable, so this strategy was built directly from <student>'s learning-gap
  data" note when `model_used === 'stub'`. `model_used` was already on the
  `InterventionSuggestion` type/serializer — no backend change needed.
- Added a friendly inline error ("Couldn't generate suggestions just now. Please
  try again in a moment.") shown when `generate.isError`.
- Extended `InterventionsPanel.test.tsx` with the AI-generated label, the stub
  Auto-strategy + note path, and the generation-error path (checklist #8).

**Verify:** Expand "Intervention Suggestions" on the teacher dashboard. With a
provider key set each card shows the ✨ AI-generated badge; with no key cards show
the Auto-strategy badge + note. Trigger a failing generate → red error line.

---

## Remaining gaps (audit notes — not yet addressed)

- **Natural language explanations** — backend `SubpartExplanationViewSet` is
  registered (`/ai/explanations/`) but is **not consumed anywhere in
  `frontend_modern`**. The post-grading student feedback surface appears to be
  unwired in the V2 app. Needs UX placement work (inline after feedback) — sizeable,
  flag before treating as polish vs. feature.
- **Interventions (`InterventionsPanel`)** — ✅ done 2026-06-08. Per-card
  `✨ AI-generated` vs `Auto-strategy` badge + stub note, plus a generation-error
  state, now consistent with `WeeklyReportPanel` and `NarrativeCard`.
- **Hint system** — solid: loading ("Thinking of a good hint…"), error, and
  exhausted states all present. Low priority.
