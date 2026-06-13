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

## 2026-06-10 — Class misconception insights: list-error state + skeleton loading

**Surface:** Class misconception insights (teacher dashboard
`MisconceptionClustersPanel`, shipped the previous day in ASA-5 / #289).

**Gaps (checklist #1 error states, #2 loading states):**
1. The list query's `isError` was never read, so a **failed fetch rendered the
   empty state** — "No misconception patterns detected yet" — telling the
   teacher their class looks clean when the server was simply unreachable.
   An error must never masquerade as an all-clear.
2. Loading was a bare "Loading misconceptions…" text line instead of the
   shape-matched skeleton its sibling student panels adopted in ASA-1, so the
   expanded section reflowed when data landed.

**Fix:**
- Destructured `isError`/`refetch` from `useMisconceptionClusters`; a failed
  fetch now shows "Couldn't load misconception patterns just now." with an
  inline **Retry** button (same pattern as `ExplanationPanel`). The empty
  state only renders on a *successful* empty response.
- Added `ClusterCardSkeleton` (mirrors the `ClusterCard` layout: label line +
  badge pill + two body lines + footer line) shown twice while loading.
- Tests: loading shows skeletons not the empty state; failed fetch shows the
  error + Retry (and not the empty state); retry recovers to real data
  (checklist #8).

**Verify:** Teacher dashboard → expand "Class Misconceptions" with the API
unreachable → red "Couldn't load…" line with Retry, not the empty state.
While loading → two pulsing card skeletons.

---

## 2026-06-10 — Interventions: list-error state + skeleton loading

**Surface:** Intervention suggestions (teacher dashboard `InterventionsPanel`).

**Gaps (checklist #1 error states, #2 loading states):**
1. The list query's `isError` was never read, so a **failed fetch rendered the
   empty state** — "No struggling students flagged yet" — telling the teacher
   no one needs help when the server was simply unreachable.
2. Loading was a bare "Loading suggestions…" text line instead of a
   shape-matched skeleton, so the expanded section reflowed when data landed.

**Fix:**
- Destructured `isError`/`refetch` from `useInterventions`; a failed fetch now
  shows "Couldn't load suggestions just now." with an inline **Retry** button
  (same recipe as `MisconceptionClustersPanel` / #291). The empty state only
  renders on a *successful* empty response.
- Added `SuggestionCardSkeleton` (mirrors the `SuggestionCard` layout: name +
  meta lines, priority pill, badge + strategy lines, chapter chips) shown
  twice while loading.
- Tests: loading shows skeletons not the empty state; failed fetch shows the
  error + Retry (and not the empty state); retry recovers to real data
  (checklist #8). Existing generate-error tests untouched.

**Verify:** Teacher dashboard → expand "Intervention Suggestions" with the API
unreachable → red "Couldn't load…" line with Retry, not the empty state.
While loading → two pulsing card skeletons.

---

## 2026-06-10 — Weekly report: list-error state + skeleton loading

**Surface:** Weekly class reports (teacher dashboard `WeeklyReportPanel`).

**Gaps (checklist #1 error states, #2 loading states):**
1. The list query's `isError` was never read, so a **failed fetch rendered the
   empty state** — "No weekly summary yet. Generate one…" — inviting the
   teacher to regenerate a report that may already exist, instead of saying
   the server was unreachable. (Only a 404 means "no report yet"; the hook
   already maps that to a successful `null`.)
2. Loading was a bare "Loading weekly summary…" text line, so the expanded
   section reflowed when the report card landed.

**Fix:**
- Destructured `isError` from `useWeeklyReport`; a failed fetch now shows
  "Couldn't load the weekly summary just now." with an inline **Retry**
  button. The empty state only renders on a *successful* `null` response.
- Added `ReportCardSkeleton` (mirrors the report card: title line + badge
  pill + 3 body lines, on the same brand-tinted card) shown while loading.
- List-error and generate-error stay visually distinct: list-error replaces
  the content area; generate-error remains the inline rose box under the
  Generate/Regenerate button.
- Tests: skeleton not the empty state while loading; failed fetch shows the
  error + Retry (and not the empty state); retry recovers to the report
  (checklist #8). Existing badge + generate-error tests untouched.

**Verify:** Teacher dashboard → expand "Weekly AI Summary" with the API
unreachable → red "Couldn't load…" line with Retry, not the generate prompt.
While loading → a pulsing report-card skeleton.

---

## 2026-06-11 — Difficulty calibration: list-error state + skeleton loading + refresh feedback

**Surface:** Difficulty calibration (teacher dashboard `QuestionQualityPanel`).
First audit of this surface — it predates the error-as-empty-state sweep and
was missed by it.

**Gaps (checklist #1 error states, #2 loading states, #8 tests):**
1. The list query's `isError` was never read, so a **failed fetch rendered the
   empty state** — "No questions flagged yet" — telling the teacher their
   question bank looks healthy when the server was simply unreachable. Same
   anti-pattern already fixed in `MisconceptionClustersPanel`,
   `InterventionsPanel`, and `WeeklyReportPanel`.
2. Loading was a bare "Loading question analysis…" text line instead of a
   shape-matched skeleton, so the expanded section reflowed when data landed.
3. The refresh mutation **silently swallowed errors** (`refresh.isError` never
   read) and gave no confirmation on success — after the button flicked back
   from "Refreshing…" nothing told the teacher a recompute was underway.
4. The panel had **no test file at all** — the only teacher AI panel without one.
5. Minor: the collapse toggle lacked `aria-expanded` (all siblings have it).

**Fix:**
- Destructured `isError`/`refetch` from `useFlaggedCalibrations`; a failed
  fetch now shows "Couldn't load the question analysis just now." with an
  inline **Retry** button. The empty state only renders on a *successful*
  empty response.
- Added `CalibrationCardSkeleton` (mirrors the `CalibrationCard` layout:
  title + meta lines, flag pill, hint line, three stat chips) shown twice
  while loading.
- `refresh.isError` → inline rose error; `refresh.isSuccess` → "Recalibrating
  from recent answers — updated verdicts appear here shortly." status line
  (same recipe as `MisconceptionClustersPanel`).
- Added `aria-expanded` to the toggle.
- New test file `QuestionQualityPanel.test.tsx` (7 tests): lazy fetch +
  skeletons, card details + summary line, empty state, list-error + Retry
  (not the empty state), retry recovery, refresh queue + status, refresh
  failure (checklist #8).

**Verify:** Teacher dashboard → expand "Question Quality" with the API
unreachable → red "Couldn't load…" line with Retry, not the empty state.
While loading → two pulsing card skeletons. Click Refresh → status line
confirms the recompute; a failing refresh shows the inline error.

---

## 2026-06-13 — Refresh confirmations self-dismiss (no stale status lines)

**Surface:** Class misconception insights (`MisconceptionClustersPanel`) and
question-quality / difficulty calibration (`QuestionQualityPanel`).

**Gap (checklist #2 loading/transient states, #3 copy/tone):**
Both panels show a reassuring status line after a teacher clicks Refresh —
"Recomputing from recent submissions…" / "Recalibrating from recent answers…".
Because the recompute runs async (Celery) there's no signal for when fresh data
lands, so the line was driven purely by `refresh.isSuccess` and **stayed on
screen indefinitely**, long after the new data had arrived. The teacher was left
staring at a "still working" message for a job that had already finished — the
"refresh confirmation lingers" gap noted in the audit since 2026-06-11.

**Fix:**
- Each panel now schedules a `setTimeout` (6s) on `refresh.isSuccess` that calls
  `refresh.reset()`, clearing the mutation's success state so the status line
  self-dismisses. Effect deps are the stable `refresh.isSuccess` / `refresh.reset`
  values (not the whole mutation object) so the timer isn't churned every render,
  and the timeout is cleared on unmount / re-trigger.
- Used the bare global `setTimeout`/`clearTimeout` (not `window.setTimeout`) so the
  timer is fake-timer/spy-friendly under happy-dom in tests.
- Added a test to each panel's spec asserting the status line disappears once the
  scheduled dismiss callback fires (checklist #8). The error/empty/skeleton paths
  are unchanged and still pass.

**Verify:** Expand "Class Misconceptions" or "Question Quality" on the teacher
dashboard and click Refresh/Calibrate. The "Recomputing…/Recalibrating…" line
appears, then clears on its own a few seconds later instead of sticking around.

---

## Remaining gaps (audit notes — updated 2026-06-13)

- ✅ **Error-as-empty-state sweep complete** — `MisconceptionClustersPanel`
  (#291), `InterventionsPanel` and `WeeklyReportPanel` (both 2026-06-10), and
  `QuestionQualityPanel` (2026-06-11, the one panel the sweep missed) now
  all distinguish a failed fetch from a genuinely empty response and use
  shape-matched skeletons while loading. `AssignmentDraftsPanel` shipped with
  the pattern built in (#297).
- **Misconception cluster cards lack AI provenance** — `sample_diagnosis` /
  `sample_remediation_tip` are copied from LLM-generated `StudentMisconception`
  rows but `ClassMisconceptionCluster` carries no `model_used`, so the cards
  can't show the `✨ AI-generated` vs stub badge used everywhere else. Needs a
  model field + migration → guardrailed out of polish runs; note for ASA.
- ✅ **Refresh confirmation lingers** — fixed 2026-06-13: `MisconceptionClustersPanel`
  and `QuestionQualityPanel` now self-dismiss the "Recomputing…/Recalibrating…"
  status line after 6s via `refresh.reset()`, instead of leaving it on screen
  after the async recompute finishes.
- **Hint system** — solid: loading ("Thinking of a good hint…"), error, and
  exhausted states all present. Low priority.
- ✅ **Unwired backend surfaces — all four groups lit.**
  `/ai/explanations/` (ASA-4, 2026-06-09), `/ai/misconception-clusters/`
  (ASA-5, 2026-06-09), `/ai/assignment-drafts/` (ASA-6, #297),
  `/ai/open-rubrics/` + `/ai/open-grades/` (ASA-7, #301 + #302). The
  repeatable audit now lives in
  [endpoint-consumer-map.md](endpoint-consumer-map.md).
- ✅ **`ExplanationPanel` provenance label** — fixed 2026-06-11 (#300): all
  five surfaces now use the shared `AIBadge` primitive from `@/shared/ui`.
- ✅ **Content recommendations click-through** — done 2026-06-09 (ASA-2).
- ✅ **SRS drill repeat-review guard** — done 2026-06-09 (ASA-3).
- ✅ **`DueForReviewPanel` skeleton/empty states** — done 2026-06-09 (ASA-1).
