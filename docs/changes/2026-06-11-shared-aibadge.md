# Shared AIBadge primitive + adoption across all AI surfaces

**Date:** 2026-06-11
**Classification:** Improve (consolidation)
**Initiative:** AI Surface Activation — continuous-improvement pool item 1

## Summary

The `✨ AI-generated` vs `Auto-…` provenance badge (initiative principle 3)
was re-implemented as a hand-rolled ternary in five places — and
`ExplanationPanel` used a bare uppercase span instead of the shared `Badge`
(a known polish-backlog inconsistency). One shared primitive now owns the
vocabulary.

## What changed

- **`frontend_modern/src/shared/ui/AIBadge.tsx`** (new) —
  `<AIBadge modelUsed stubLabel? className?>`: brand-toned `✨ AI-generated`
  for a real LLM, neutral surface-specific `Auto-…` label when
  `model_used === 'stub'`.
- **`frontend_modern/src/shared/ui/aiProvenance.ts`** (new) — `isAIStub()`
  helper (separate file keeps the component file fast-refresh-clean); panels
  use it for their contextual stub notes.
- Exported from `ui/index.ts`; showcased on the `/design` route per the
  design-system rule.
- **Adopted in all five call sites** (labels unchanged, so every existing
  badge test still passes as-is):
  - `InterventionsPanel` — `Auto-strategy`
  - `WeeklyReportPanel` — `Auto-summary`
  - `parent/components/NarrativeCard` — `Auto-summary`
  - `ExplanationPanel` — `Auto-explanation` (was a bare span → now the shared
    Badge, closing the polish-backlog item)
  - `AssignmentDraftsPanel` — `Auto-drafted`
- The per-surface stub *notes* ("AI was unavailable, so this was built
  from …") intentionally stay in the panels — they are contextual copy, not
  badge vocabulary.

## Tests

New `AIBadge.test.tsx` (4 cases: LLM label, stub label, default label,
`isAIStub` edge cases). All 5 adopting components' suites re-run green
(38 tests across 6 files). Lint + tsc clean.

## Notes

Stacked on the #294 re-land (PR #299) because both touch
`WeeklyReportPanel.tsx`.
