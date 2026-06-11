# AI Surface Activation

**Status:** 🟢 Active (promoted 2026-06-09)
**Owner docs:** [`docs/ai-features/polish-backlog.md`](../ai-features/polish-backlog.md) (audit trail that seeded this initiative)

## North Star

**Every AI capability the backend already ships is reachable, polished, and
honest in the product.** The 2026-06-09 audit found four fully-built, tested AI
endpoint groups with **zero frontend consumers** (`/ai/explanations/`,
`/ai/misconception-clusters/`, `/ai/assignment-drafts/`,
`/ai/open-rubrics/` + `/ai/open-grades/`), plus shipped AI panels with inert or
inconsistent edges. That is paid-for product value sitting dark. This
initiative wires each orphaned surface into the right student/teacher/parent
moment — and finishes the consistency pass on the surfaces already live — until
**no AI endpoint is orphaned and every AI surface meets the 8-point polish
checklist**.

Who it's for: students get explanations and a practice loop that closes;
teachers get class-level misconception insight and AI-drafted assignments;
the platform earns trust by always labelling what is AI vs. data-derived.

## Principles

1. **Activation over invention.** Prefer wiring an existing, tested backend to
   building any new AI capability. No new models/endpoints unless a surface
   genuinely needs a missing field.
2. **The 8-point polish checklist is the bar** (error/degradation, loading,
   copy/tone, empty states, placement, V2 design, provider-cascade
   transparency, test coverage) — every increment ships meeting it, not as a
   follow-up.
3. **Provider transparency always**: `✨ AI-generated` (brand tone) for a real
   LLM, neutral `Auto-…` badge + plain-language note when `model_used ===
   'stub'`. Same `Badge` vocabulary as `WeeklyReportPanel` / `NarrativeCard` /
   `InterventionsPanel`.
4. **Async means visible progress.** Generation endpoints are queue-based
   (202 + poll). Surfaces show a working state and recover from failure with a
   friendly retry line — never a silent swallow.
5. **Close the loop.** An AI insight that can't be acted on in one click
   (practice this chapter, approve this draft) is half-shipped.

## Foundation / Scaffold (what already exists)

- **Backend (all tested, all live):** `SubpartExplanationViewSet`
  (`/ai/explanations/` + `generate/` → 202, poll list),
  `ClassMisconceptionClusterViewSet` (`/ai/misconception-clusters/` +
  `refresh/`), `AssignmentDraftViewSet` (`/ai/assignment-drafts/` +
  `generate/`/`approve/`/`dismiss/`), `OpenResponseRubricViewSet` +
  `OpenResponseGradeViewSet`. LLM cascade with deterministic stub fallback and
  `model_used` on serializers.
- **Frontend patterns to copy:** `RecommendationsPanel` (skeleton/empty/error,
  [#283](https://github.com/openshiksha/openshiksha/pull/283)),
  `InterventionsPanel` (collapsible teacher panel + generate + AI badge),
  `AIHintPanel` (per-subpart in-card AI affordance), `WeeklyReportPanel`
  (generate + poll + badge). Shared `Badge`, `Skeleton`, `Button` in
  `src/shared/ui`.
- **Routes:** `/student/browse/chapter/:chapterId` (BrowsePracticePage) is the
  canonical "practice this chapter now" target, available to both `student`
  and `open_student`.

## Backlog (session-sized increments)

| ID | Increment | Status |
|----|-----------|--------|
| ASA-1 | `DueForReviewPanel` consistency: loading skeleton + explanatory empty state (same pattern as #283) | ✅ [#285](https://github.com/openshiksha/openshiksha/pull/285) |
| ASA-2 | Recommendation rows click-through → `/student/browse/chapter/:id` ("Practice" affordance per row) | ✅ [#286](https://github.com/openshiksha/openshiksha/pull/286) |
| ASA-3 | SRS drill repeat-review guard: second pass in one sitting is practice-only, never a second SM-2 update | ✅ [#287](https://github.com/openshiksha/openshiksha/pull/287) |
| ASA-4 | Wire `/ai/explanations/` into post-submit assignment feedback (per-subpart "Explain" → generate → poll → labelled explanation) | ✅ [#288](https://github.com/openshiksha/openshiksha/pull/288) |
| ASA-5 | Teacher `MisconceptionClustersPanel` on dashboard (list + refresh + AI labels) | ✅ [#289](https://github.com/openshiksha/openshiksha/pull/289) |
| ASA-6 | Assignment draft builder UI (`/ai/assignment-drafts/`): generate → review rationale → approve into a real Assignment / dismiss | ✅ [#297](https://github.com/openshiksha/openshiksha/pull/297) |
| ASA-7 | Open-response grading UI (`/ai/open-rubrics/` + `/ai/open-grades/`) — teacher review surface | ☐ |
| ASA-8 | Explanations on the SRS drill result screen (reuse ASA-4's hook/panel) | ✅ [#296](https://github.com/openshiksha/openshiksha/pull/296) |
| ASA-9 | Backend idempotency guard for repeat SRS review in one day (defence-in-depth behind ASA-3) | ✅ [#295](https://github.com/openshiksha/openshiksha/pull/295) |

## Definition of Done (per increment)

- Meets all 8 polish-checklist points, incl. provider-transparency badges and
  a tested error path.
- Build/lint/types/tests green (`npm run lint && npx tsc --noEmit && npx vitest run`,
  `pytest` if backend touched). New UI has a Vitest file.
- V2 design language only (`os-card`, `ink`/`brand` tokens, shared `Badge`/`Skeleton`).
- Ledger row appended below; `STATUS.md` headline updated when a phase lands.

**Initiative DoD (North Star reached):** no `/ai/` endpoint group without a
frontend consumer; every AI surface passes the checklist audit; recommendations
→ practice loop closes in one click.

## Continuous Improvement pool

- Unify the `✨ AI-generated` / `Auto-…` badge + stub-note into one shared
  `AIBadge` component (currently re-implemented in 3+ panels).
- Extract a `useAsyncGeneration` hook for the POST-202-then-poll pattern.
- Sweep remaining raw `<a href>` SPA-internal links in feature panels.
- Add an `/ai/` endpoint-to-consumer map in `docs/ai-features/` and keep it
  current (the audit that found this gap should be repeatable).

## Progress Ledger

| Date | Increment | PR | Learning |
|------|-----------|----|----------|
| 2026-06-09 | Initiative promoted; ASA-1..5 planned as today's batch | — | Seeded by the polish-backlog audit: 4 endpoint groups had no consumer. |
| 2026-06-09 | ASA-1 — DueForReviewPanel skeleton + empty state | [#285](https://github.com/openshiksha/openshiksha/pull/285) | `useSpacedRepetitionDue` already exposed `isLoading`/`isError`; pure pattern copy from #283. |
| 2026-06-09 | ASA-2 — recommendation rows → chapter practice | [#286](https://github.com/openshiksha/openshiksha/pull/286) | `chapter` was on the payload all along; pill styling shared with DueForReviewPanel keeps the action language consistent. |
| 2026-06-09 | ASA-3 — SRS repeat-review guard | [#287](https://github.com/openshiksha/openshiksha/pull/287) | Plan's "grade locally" assumption was wrong (no client-side correctness); practice rounds are unscored — the guard (one SM-2 update per sitting) is what matters. ASA-9 stays for defence-in-depth. |
| 2026-06-09 | ASA-4 — post-submit answer explanations | [#288](https://github.com/openshiksha/openshiksha/pull/288) | Serializer lacked `model_used` (1-line fix). Per-subpart correctness doesn't exist in the API — derived conservatively from overall score; per-subpart grade breakdown is a backlog candidate. |
| 2026-06-09 | ASA-5 — teacher misconception clusters panel | [#289](https://github.com/openshiksha/openshiksha/pull/289) | Cluster serializer has no `model_used` (aggregation, not generation) — no badge needed. InterventionsPanel pattern copied wholesale; 2 of 4 dark endpoint groups now lit. |
| 2026-06-10 | Polish — `InterventionsPanel` list-error + skeletons | [#293](https://github.com/openshiksha/openshiksha/pull/293) | Pure pattern copy of #291; `useQuery` already exposed `isError`/`refetch`. |
| 2026-06-10 | Polish — `WeeklyReportPanel` list-error + skeletons | [#294](https://github.com/openshiksha/openshiksha/pull/294) | Stacked on #293 (shared polish-backlog doc). Error-as-empty-state sweep now **complete** across all teacher AI panels. Hook's 404→null mapping meant only real failures hit the error path. |
| 2026-06-10 | ASA-9 — server-side same-day SM-2 guard | [#295](https://github.com/openshiksha/openshiksha/pull/295) | "Grade, don't schedule": guarded calls still grade answers but skip schedule/ticks/streak. Additive `already_reviewed_today` flag; no migration needed. |
| 2026-06-10 | ASA-8 — explanations on drill result screens | [#296](https://github.com/openshiksha/openshiksha/pull/296) | Zero new hooks — rendering the answered questions read-only via `QuestionCard` unlocked ASA-4's ExplanationPanel *and* worked-solution reveal for free. Practice rounds pass `null` score (ungraded client-side). |
| 2026-06-10 | ASA-6 — assignment drafts panel (batch anchor) | [#297](https://github.com/openshiksha/openshiksha/pull/297) | 3 of 4 dark endpoint groups lit; only ASA-7 remains. Per-room mounting beat the planned room-dropdown (siblings set the convention). Third re-implementation of 202-then-poll — `useAsyncGeneration` extraction is now clearly worth it. |
