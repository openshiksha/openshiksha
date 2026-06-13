# LA-6e-4 — CreateQuestionPage in Hindi (closes LA-6)

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** Language Access (2026-language-access.md) — LA-6e (final slice)

## Summary

Localized `CreateQuestionPage` (1131 lines) — the single most-used teacher
authoring screen and the last English-only teacher surface. Chrome strings only:
the variable-substitution, KaTeX rendering, and constraint-evaluation logic are
untouched. With this, the entire teacher product renders in Hindi and **LA-6 is
closed**.

## Legacy reference

Legacy `sphinx/` was the question-authoring UI (Django templates, English only,
no i18n). Pure "improve" — nothing to port.

## What changed

All five components in the file now translate via `useT()`:

- **`WidgetPickerSection`** — widget label/hint, fields-configured count
  (sing/plural), edit/remove, add-widget.
- **`renderPreview`** (helper) — now takes `t` for the empty-preview placeholder.
- **`VariablePreview`** — preview label, Student A/B sample lines.
- **`DraftCard`** — draft badge, "Use this", answer label. (Renamed an inner
  `.map((t) =>` to `.map((tag) =>` to avoid shadowing the translate fn.)
- **`AIGenerationPanel`** — panel title/subtitle, topic label/placeholder,
  type/difficulty/count labels, type options, generate/generating, failure +
  retry, AI-unavailable notice, drafts-count (sing/plural).
- **`CreateQuestionPage`** (main) — header (create/edit title + subtitle), back,
  success state (created/updated + body + create-another / back-to-bank), chapter
  card (subject/chapter selects + options + difficulty + hint), subpart tabs +
  add-part, question type (long labels), question text label/LaTeX hint/variable
  hint/placeholders, preview, image URL + upload + formats + error + alt, worked
  solution, hint, variable-constraints panel (min/max/integer), MCQ options,
  correct answer (+ token hint, select/numeric placeholders), remove-part, submit
  (save/update + can't-submit hint + save-failed).

LaTeX-bearing hints (`$x^2$`, `\frac{a}{b}`, `{{a}}` tokens) are kept verbatim in
both locales; the `{var}` interpolator is a no-op when `t()` is called without
vars, so the literal braces survive.

- **Locale files** — ~95 new keys in both `en.ts`/`hi.ts` under a single LA-6e-4
  (`cqp.*`) section. Type labels use a page-local `cqp.type*` set (not the
  in-flight LA-6e-2 `qtype.*`) so this PR stays independent of #324. Glossary
  register: प्रश्न, उपभाग/भाग, चर, बाधा, कठिनाई. Parity guard stays green.

## Tests

- Added `CreateQuestionPage.test.tsx` (the page had **no test**) — create-mode
  heading renders in English by default + a renders-in-Hindi case (mocks the
  shared apiClient so the form renders without network).
- Full suite green: 60 files / 376 tests. Lint + tsc clean. Build under budget
  (entry 137 kB).

## Next steps

LA-6 + LA-8 are now closed. Remaining: LA-9 (third-language pilot), LA-10
(authored-content translation, blocked on product design). Update the initiative
ledger + STATUS.md headline to "LA-6 + LA-8 closed — only LA-9/LA-10 remain".
