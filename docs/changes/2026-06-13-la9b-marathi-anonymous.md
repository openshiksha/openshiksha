# LA-9b — Marathi seat + anonymous journey

**Date:** 2026-06-13
**Classification:** New (content) + small backend
**Initiative:** Language Access — depends on LA-9a (#349)

## Summary

Registers **Marathi (मराठी)** as the platform's third UI locale — the proof
that, after LA-9a's registry, a new language is a *content task, not an
engineering task*. The switcher now shows **EN | हिं | मरा** with no switcher
edit. Ships `locales/mr.ts` as a **pilot subset** covering the anonymous journey
(common / auth hero / login / register — ~45 keys); everything else falls back
to English at runtime (principle 3).

## What changed

- **`locales/registry.ts`** — widened `Locale` to `'en' | 'hi' | 'mr'`; added the
  `mr` `LOCALES` entry (`coverage: 'pilot'`, `intlLocale: 'mr-IN'`, Devanagari
  font via `htmlLang: 'mr'`) and its lazy `localeLoaders.mr` import. That is the
  *entire* engineering surface for the new language.
- **New `locales/mr.ts`** — Marathi anonymous-journey dictionary, typed
  `satisfies Partial<LocaleDict>` so every key is checked against English while
  permitting a subset.
- **Backend `core.models.User.preferred_language`** — added `("mr", "Marathi")`
  to choices + migration `0028_alter_user_preferred_language`. The profile
  serializer is a `ModelSerializer`, so it picks up the new choice automatically.
- **`types/index.ts`** — `User.preferred_language` now references the i18n
  `Locale` type instead of a hardcoded `'en' | 'hi'`, so it tracks the registry.
- **AI-language clamp (frontend half of LA-9d)** — registering `mr` made the
  `Locale` union reach the AI explanation/parent-summary request types
  (`'en' | 'hi'`). Added `shared/i18n/aiLanguage.ts` (`AiLanguage` +
  `toAiLanguage`), which maps an unsupported locale (`mr`) to English so a pilot
  user never sends a language the LLM prompt can't honor. Applied at the three
  call sites (`ExplanationPanel` ×2, `ParentInsightsPage`). The **backend**
  guard + email resolver remain LA-9d.

## Tests

- New frontend cases (`i18n.test.tsx`): renders Marathi anonymous-journey
  strings; falls back to English for an untranslated key; `<html lang="mr">`
  syncs; switcher renders three buttons (`EN | हिं | मरा`) and selects Marathi.
- Backend: `test_student_can_set_preferred_language` parametrize gains `"mr"` —
  round-trips through `PATCH /api/v1/users/me/profile/`.
- `tsc --noEmit` clean · `eslint` clean · `vitest run` → 394 passed ·
  `pytest test_profile_api.py` → 13 passed · `manage.py check` clean.

## Migration notes

`0028_alter_user_preferred_language` only widens a `choices` list — no schema
change, fully non-breaking.

## Next steps

LA-9c: extend `mr.ts` with the student core loop + date-fns `mr` relative dates.
LA-9d: the backend AI/email `mr → en` fallback guard (this PR did the frontend
clamp only).
