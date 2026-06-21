# LA-4 — AI content in the reader's language

**Date:** 2026-06-11
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-4)

## Summary

AI-generated content now follows the active locale. Answer explanations
generate in the reader's language (with an in-place regenerate affordance when
a stored explanation is in the "wrong" language), and the parent weekly
summary generate call passes the active locale instead of hardcoded `'en'` —
closing the last stale ROADMAP item ("AI explanations in Hindi: backend
supports it, UI doesn't expose it").

## Legacy files referenced

None — no legacy equivalent (AI features are modern-only).

## What changed and why

**Frontend**
- `useGenerateExplanation` payload gains `language?: 'en' | 'hi'`.
- `ExplanationPanel`:
  - passes the active locale on generate (initial generation).
  - **Panel honesty**: if the stored explanation's `language` ≠ active locale,
    the text still renders (never block content), tagged with `lang=` for
    screen readers, plus a "हिंदी में समझाएँ" / "Explain in English"
    regenerate button. Regeneration reuses the existing poll loop, now keyed
    on "row exists in the requested language" rather than just "row exists".
  - panel chrome itself migrated to `t()` (9 new `explanation.*` keys).
- `ParentInsightsPage` passes the active locale on the summary generate call
  (`useParentSummary` already typed `language`; no caller sent it).

**Backend**
- No production change needed: `generate_explanation_for_subpart` already
  `update_or_create`s on `(student, subpart, submission)` with `language` in
  defaults, so a different-language request regenerates the same row. Two new
  tests pin that contract (regenerate-in-place on language change; idempotent
  on same language) so it can't silently regress.

## Tests

- Backend: `test_explanations.py` +2 (25 passed).
- Frontend: `ExplanationPanel.test.tsx` +3 (generate body carries the locale;
  stale-language row renders with working regenerate flow; no affordance when
  languages match) and the existing generate-body assertion extended with
  `language: 'en'`. Full suite 54 files / 348 tests green; lint/tsc/build/
  budget green (entry 100.96 kB).

## Migration notes

None.

## Next steps

LA-5 (parity guard + parent/registration/home chrome). LA-7 will localize the
transactional emails using `preferred_language`.
