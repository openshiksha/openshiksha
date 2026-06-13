# LA-6e-1 — authoring preview & edit-safety chrome in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** Language Access (2026-language-access.md) — LA-6e

## Summary

Localized four teacher authoring-safety surfaces that were still hardcoded
English: the assignment **snapshot preview**, the **re-sync modal**, the
**edit-safety banner**, and the **problem-set preview page**. Chrome strings only
— authored content, student responses, AI/diff payloads, and the math rendering
are untouched (Principle 1). After this, a Hindi-medium teacher previewing what
students see, diffing a drifted assignment, or editing a live problem set stays
in Hindi.

## Legacy reference

None — legacy Django 1.11 had no teacher i18n. Pure "improve".

## What changed

- **`EditSafetyBanner.tsx`** — replaced the free-text `noun="this question"` prop
  with a typed `subject?: 'question' | 'problemSet'` so the headline is a proper
  localized full sentence (English capitalization / Hindi word order both work).
  Body copy now keys off `editSafety.body` / `editSafety.bodyGraded`. The inline
  `<strong>future</strong>` emphasis was folded into the translated sentence (a
  translated sentence can't carry mid-string markup cleanly across languages).
- **`AssignmentSnapshotPreview.tsx`** — heading, frozen note, show/hide, drift
  banner + compare link, update action, undo bar.
- **`ResyncAssignmentModal.tsx`** — title/subtitle, load/no-drift/apply errors,
  regrade note (singular/plural), apply-button states, and the `DiffSummary`
  added/removed/answer/content lines (singular/plural keys).
- **`ProblemSetPreviewPage.tsx`** — mode banner, edit/preview toggle, confirm
  dialogs, header question-count (reuses `teacher.minutesApprox`), empty states,
  per-question edit/remove, add-more block, footer buttons.
- **Locale files** — ~55 new keys added to both `en.ts` and `hi.ts` under LA-6e-1
  sections. Glossary register: असाइनमेंट, समस्या सेट, स्नैपशॉट, संस्करण, प्रश्न.
  Parity guard stays green.

## Tests

- Updated `EditSafetyBanner.test.tsx` to the new `subject` prop + a hi-render case.
- Added a renders-in-Hindi case to `AssignmentSnapshotPreview.test.tsx`,
  `ResyncAssignmentModal.test.tsx`, `ProblemSetPreviewPage.test.tsx` (wrap in
  `<I18nProvider initialLocale="hi">`, `waitFor` the lazy Hindi dict, assert a
  Glossary Hindi string).
- Full suite green: 57 files / 361 tests. Lint + tsc clean. Build under budget.

## Next steps

LA-6e-2 (question bank, preview, record-response, widget gallery), LA-6e-3
(versions + classroom code — uses LA-8 `formatDate`), LA-6e-4 (CreateQuestionPage).
