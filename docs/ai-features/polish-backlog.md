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

## 2026-06-09 — Content recommendations: loading skeleton + empty state + SPA links

**Surface:** Content recommendations (student dashboard `RecommendationsPanel`).

**Gaps (checklist #2 loading states, #4 empty states, #6 V2 consistency):**
1. The panel returned `null` while loading, so on every dashboard visit the
   card **popped in after the fetch** and shoved the "Due for Review" panel
   down — exactly the flash-of-empty-space the checklist forbids.
2. With zero recommendations the panel rendered nothing at all, so a new
   student **never learns the feature exists** and gets no explanation of what
   unlocks it (checklist #4: never a blank section without explanation).
3. Errors were silently swallowed into the same hidden state (now an explicit,
   commented decision: the assignments list already surfaces connectivity
   problems, so the panel steps aside on error rather than stacking banners).
4. Footer links used raw `<a href>` → **full page reloads** instead of SPA
   navigation; priority chips were hand-rolled spans instead of the shared
   `Badge`. The bare score percentage had no label.

**Fix:**
- Added a shape-matched `Skeleton` card (header + 3 rows) during load.
- Added a compact empty-state card: "No suggestions yet — answer a few
  assignment questions and we'll point you to the chapters worth revisiting."
- Replaced `<a>` with react-router `Link`; priority chips now use the V2
  `Badge` (1=urgent, 2=attention, 3=brand, 4=neutral); score now labelled
  "your score".
- New test file `RecommendationsPanel.test.tsx` covers the skeleton, the
  populated render, the empty state, and the hide-on-error path (checklist #8).

**Verify:** Student dashboard → "What to Practice Next" shows a skeleton while
loading, real rows with badges + labelled scores when data exists, and the
explanatory empty card for a fresh student. Footer links navigate without a
full reload.

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
- **Unwired backend surfaces (2026-06-09 audit)** — besides `/ai/explanations/`,
  three more AI endpoints have **no `frontend_modern` consumer at all**:
  `/ai/misconception-clusters/` (class misconception insights),
  `/ai/assignment-drafts/` (assignment draft builder), and
  `/ai/open-rubrics/` + `/ai/open-grades/` (open-response grading). Wiring each
  is UI-build work, not polish — flagging here rather than building.
- **Content recommendations rows are inert** — each row shows chapter + reason
  but offers no click-through to actually practice that chapter
  (`problem_set` is on the payload but unused). Needs a routing decision
  (browse-by-chapter vs problem-set link); small feature, not pure polish.
- **SRS drill result screen** — "Review again" lets a student immediately
  resubmit the same drill, which re-runs the SM-2 update and can double-move
  the interval in one sitting. Worth a guard or copy tweak on a future run.
- **`DueForReviewPanel`** — same render-`null`-while-loading pop-in pattern
  that was just fixed on `RecommendationsPanel`; lower impact (panel is below
  the fold) but should be made consistent on a future run.
