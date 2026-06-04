# 2026-06-03 — Proficiency cluster migrated to V2

## Summary
Migrated the student proficiency cluster: `ProficiencyPage.tsx`, `StreakBadge.tsx`,
and the two dashboard child panels `DueForReviewPanel.tsx` + `RecommendationsPanel.tsx`.
Mastery now reads as the "unlock" motif — brand-600 fill at >=70% with a check glyph.

## Classification
Improve — reskin + a touch of motif (unlock check) on mastery rows.

## What changed
- `ProficiencyPage`: SectionHeading, Card, EmptyState; ink/brand tokens; mastery
  bar in `brand-600` + check glyph (unlock motif).
- `StreakBadge`: tier palette swung to brand/amber tokens (orange/yellow/amber/purple →
  brand/amber/amber/brand) — escalates within the brand language.
- `DueForReviewPanel`: red/blue → rose/brand; `os-card` with amber warning border.
- `RecommendationsPanel`: priority badges and links to ink/brand tokens; warm divider.
- `motion-reduce:transition-none` + focus-visible rings on the Practice CTA.

## Tests
- type-check / lint / build / vitest 84/84 — green.

## Verify
`student_demo` / `demo1234` → /student (dashboard panels) and /student/proficiency.

## Next
PR5 will migrate Assignment detail + SRS drill + shared cards.
