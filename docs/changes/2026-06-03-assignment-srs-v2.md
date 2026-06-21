# 2026-06-03 — Assignment detail + SRS drill migrated to V2

## Summary
Migrated the highest-traffic student practice flow to V2 "Chalk & Unlock":
`AssignmentDetailPage.tsx`, `SRSDrillPage.tsx`, and the shared `QuestionCard.tsx`,
`AssignmentCard.tsx`, `AssignmentList.tsx`.

## Classification
Improve — reskin + light unlock motif on score reveals. Auto-save debounce, submit
logic, and `RichContent`/`InteractiveWidget` wiring untouched.

## What changed
- `QuestionCard`: warm `.os-card`; MCQ/multi-select selected state =
  `brand-500` border + `brand-50` fill; numeric/fill_blank use `.input-brand`;
  solution reveal is brand-tinted (the "unlock" of the answer), hints stay amber.
- `AssignmentDetailPage`: progress bar brand-500 on ink-100 track; post-submit
  score card uses the unlock-motif palette (emerald/amber/rose) and is heading-styled
  in Fraunces; confirm dialog uses `.os-card` chrome + `<Button>` actions.
- `SRSDrillPage`: result card retains emerald/amber semantic surfaces, primary
  CTAs use `<Button variant="brand"|"ghost">`, "Back to dashboard" link styles
  to `.btn-brand`. Empty + error states swapped for `<EmptyState>`.
- `AssignmentCard`: status pills → `<Badge>` (success/attention/urgent),
  `<Button>` CTA; progress bar = brand-500 (unlock motif).
- `AssignmentList`: empty state → `<EmptyState>`; section accent pills
  recoloured to brand/amber/rose/emerald tokens. **Section heading text
  ("Overdue", "Due Soon", "Upcoming", "Completed") and empty-state phrase
  preserved exactly** so `AssignmentList.test.tsx` keeps passing.
- QuestionCard radio `name` attribute (`subpart-<id>`), placeholder
  ("Enter your answer"), and `type="number"`/`type="text"` preserved verbatim —
  every assertion in `QuestionCard.test.tsx` still holds.
- `motion-reduce:transition-none` + focus-visible rings throughout.

## Tests
- `npm run type-check` — green
- `npm run lint` — green
- `npm test -- --run` — 84/84 (incl. `QuestionCard.test.tsx` 4/4 and
  `AssignmentList.test.tsx` 6/6) — green
- `npm run build` — green

## Verify
Log in as `student_demo` / `demo1234`:
1. /student → assignment cards now use unlock-motif progress and brand CTAs
2. Open an assignment → answer MCQ + numeric → submit → see the brand/emerald
   score reveal
3. /student/srs/drill/<id> → drill UI, submit → result card

## Closes
M4-05 in the V2 design system rollout. After this PR, only `M4-07` (teacher
authoring cluster) remains in the M4 product-surface migration.
