# ASA-4 — Post-submit answer explanations (first consumer of /ai/explanations/)

**Date**: 2026-06-09
**Classification**: New
**Initiative**: AI Surface Activation (ASA-4)

## Summary

The `/ai/explanations/` endpoint group (generate + list, fully built and
tested on the backend) had zero frontend consumers. Students now get an
"✨ Explain this answer" affordance per subpart after submitting an
assignment — the platform's first surface that explains *why* an answer was
right or wrong, not just the mark.

## Legacy reference

None — legacy showed marks only after grading; no explanation capability ever
existed. This is the "improve, don't just migrate" thesis applied to the core
grading loop.

## What changed

**Backend (one line)**
- `SubpartExplanationSerializer` now exposes `model_used` so the frontend can
  apply the standard AI/stub provenance badge (same vocabulary as
  `NarrativeCard`/`InterventionsPanel`/`WeeklyReportPanel`). The plan assumed
  the field was already serialized; it wasn't.

**Frontend**
- `useExplanation.ts` (new): `useExplanationList(subpartId, enabled)` — GET
  `/ai/explanations/?subpart=<id>`, handles both list and paginated shapes,
  `staleTime: Infinity` (explanations persist server-side);
  `useGenerateExplanation()` — POST `/ai/explanations/generate/` (202, async
  Celery task).
- `ExplanationPanel.tsx` (new): collapsed trigger → on click checks for an
  existing explanation (shows it directly, never re-generates) → otherwise
  fires generate exactly once and polls the list (default 2 s cadence, 15
  attempts ≈ 30 s budget) → renders the explanation with `✨ AI-generated`
  badge, or `Auto-explanation` + stub note when `model_used === 'stub'`.
  Timeout/API failure → friendly inline error with a working Retry. Poll
  cadence and budget are props, overridable for tests.
- `QuestionCard.tsx`: new optional `explanationScore` prop (graded
  submission's 0–1 score). When provided and `isSubmitted`, mounts
  `ExplanationPanel` after the worked solution per subpart.
- `AssignmentDetailPage.tsx`: passes `explanationScore={submitScore}`.

## Correctness caveat (documented decision)

Per-subpart correctness is not exposed anywhere in the API (`Submission` has
only an overall `score`). Per the plan's fallback, `is_correct` sent to the
generator is derived from the overall score — `true` only on a perfect score.
Conservative on purpose: for partially-correct submissions the explanation
takes the "where this went wrong" framing, which still teaches even if that
particular subpart happened to be right. A per-subpart grading breakdown is a
candidate backlog item.

## Tests

- `ExplanationPanel.test.tsx` (5 tests): trigger→generate→poll→render;
  existing-explanation short-circuit (no POST); stub badge + note; poll-budget
  timeout with working retry; generation failure surfaces instead of polling
  forever.
- Backend: `pytest openshiksha/apps/ai/` — 357 passed (serializer change
  covered by existing list/retrieve tests).
- Full frontend suite 265 passed; `tsc --noEmit`, `eslint`, `vite build` clean.

## Migration notes

No model/migration changes — serializer-only on the backend.

## Next steps

ASA-5 (misconception clusters panel) closes today's batch. ASA-6/7 (assignment
drafts, open-response grading) remain the next dark surfaces.
