# LA-6e-2 — question bank, preview, record-response & widget gallery in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** Language Access (2026-language-access.md) — LA-6e

## Summary

Localized four high-traffic teacher surfaces: the **question bank** (+ its
add-to-set sheet), the **question preview panel**, the **record-response / rubric**
authoring panel that feeds the AI grading queue, and the **widget gallery**.
Chrome strings only — question text, MCQ options, math (KaTeX), AI-suggested
rubric text, student responses, and sandboxed widget content all render as-is
(Principle 1). Filter/search state logic untouched.

## Legacy reference

None — legacy Django 1.11 had no teacher i18n. Pure "improve".

## What changed

- **`questionPreviewMeta.ts`** — added `localizedTypeLabel(t, type)` mapping the six
  question types to `qtype.*` keys (MCQ stays "MCQ" per Glossary). `typeLabel`
  kept for the still-English `CreateProblemSetPage`.
- **`QuestionPreviewPanel.tsx`** — part labels, image alt, numeric/fill-blank
  notes, interactive-widget note, type badge, difficulty title, and the default
  empty-state (now computed via `t()` when not overridden).
- **`QuestionBankPage.tsx`** — header, search placeholder, all filter
  labels/options (subject/difficulty/chapter), clear-filters, results count
  (singular/plural), empty states, row + footer actions, and the full
  **add-to-problem-set sheet** (title, success, no-sets, per-set count, errors).
- **`RecordResponsePanel.tsx`** — the rubric form (max marks, model answer,
  marking points + sum-mismatch warning, save/update), the rubric summary, and
  the record-response form (class/student/question selects with their loading and
  placeholder states, success/error notes, submit button).
- **`WidgetGalleryPanel.tsx`** — gallery heading/description, no-widgets state,
  answer badge, no-schema banner, back-to-gallery, Config/Preview labels, preview
  note, use-this-widget. Schema field *names* stay as authored (technical).
- **Locale files** — ~115 new keys in both `en.ts` and `hi.ts` under LA-6e-2
  sections (`qtype.*`, `qbank.*`, `addToSet.*`, `qpreview.*`, `widgetGallery.*`,
  `recordResp.*`). Glossary register: प्रश्न बैंक, कठिनाई, अध्याय, रूब्रिक, समस्या सेट,
  विषय. Parity guard stays green.

## Tests

- Added a renders-in-Hindi case to `QuestionBankPage.test.tsx`,
  `RecordResponsePanel.test.tsx`, `WidgetGalleryPanel.test.tsx`.
- Added a new `QuestionPreviewPanel.test.tsx` (it had none) — English empty-state +
  a Hindi type-badge case.
- Full suite green: 58 files / 362 tests. Lint + tsc clean. Build under budget
  (entry 128 kB).

## Next steps

LA-6e-3 (versions + classroom code — uses LA-8 `formatDate`), LA-6e-4
(CreateQuestionPage).
