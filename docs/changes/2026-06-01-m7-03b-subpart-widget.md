# M7-03b — Frontend per-subpart input widget

## Summary

The student `QuestionCard` now selects each subpart's input widget from
`subpart.subpart_type` (falling back to `question.question_type`), so a single
`compound` question renders the right control per subpart — e.g. an option list
for an mcq subpart and a numeric input for a numeric subpart.

## Classification

**Improve** — depends on **M7-03a** ([#128](https://github.com/openshiksha/openshiksha/pull/128))
which serializes `subpart_type`.

## What changed

### Types — `frontend_modern/src/types/index.ts`
- New `SubpartType` union (mirrors backend `QuestionType`).
- `QuestionSubpart.subpart_type?: SubpartType | ''` (blank for legacy rows).
- `Question.question_type` widened to `SubpartType | 'compound'`.

### Component — `frontend_modern/src/features/student/QuestionCard.tsx`
- `SubpartInput` now takes `widgetType` instead of the whole-question type and
  dispatches on it (mcq / multi_select / numeric / text fallback).
- Call site passes `subpart.subpart_type || question.question_type` so legacy/
  hand-authored rows (blank `subpart_type`) keep working, and a `compound`
  parent type never reaches the widget (each subpart resolves its own type).

## Tests

`QuestionCard.test.tsx` (new, 4 tests):
- A compound question with mcq + numeric subparts renders a radio list and a
  numeric input respectively.
- Blank `subpart_type` falls back to the parent question type.
- multi_select → checkboxes; fill_blank → text input.

Frontend: type-check, lint, build, and full Vitest suite (**46 passed**) green.

## Migration notes

None — frontend only.

## Next steps

- PR 5: `audit_cabinet_fidelity` command + DoD regression test (the wrong-widget
  metric is now meaningfully checkable since the widget reads `subpart_type`).
