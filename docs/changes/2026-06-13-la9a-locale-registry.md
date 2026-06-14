# LA-9a — N-locale framework + pilot-coverage parity model

**Date:** 2026-06-13
**Classification:** New / hardening (foundation for LA-9 third-language pilot)
**Initiative:** Language Access (`docs/initiatives/2026-language-access.md`)

## Summary

Generalized the hardcoded binary `en | hi` i18n machine into an N-locale
**registry** that every consumer reads from, and replaced the all-or-nothing
parity guard with a **pilot-coverage** contract. This pays the engineering tax
once so that adding a third language (Marathi, LA-9b+) is a pure content task —
the initiative North Star's "a third language must be a content task, not an
engineering task."

**Zero behavior change for en/hi:** every pre-existing i18n test
(`i18n.test.tsx`, `format.test.ts`, the switcher test) passes **unedited**, the
`hi` dictionary still splits into its own lazy chunk (75 kB), and the entry
chunk is unchanged at 140 kB (160 kB budget holds).

## What changed

- **New `frontend_modern/src/shared/i18n/locales/registry.ts`** — the single
  source of truth: `LOCALES` (per-locale `label`, `nativeName`, `htmlLang`,
  `intlLocale`, `coverage`), `localeMeta()`, `isLocale()`, `localeLoaders` (lazy
  dict loaders; English is eager and intentionally absent), and `DEFAULT_LOCALE`.
  Registers only `en` + `hi`, both `complete` — the empty third seat is the
  proof that a new language is now additive.
- **`i18nContext.ts`** — `Locale` and `isLocale` now come from the registry
  (re-exported for back-compat); `resolveInitialLocale` falls back to
  `DEFAULT_LOCALE`.
- **`I18nProvider.tsx`** — single `hiDictCache` + hardcoded `import('./locales/hi')`
  replaced with a `Map<Locale, LoadedDict>` cache and a generic loader driven by
  `localeLoaders[locale]`. Loaded dicts are typed as a `Partial` of the English
  key set so a **pilot** locale can be a subset (English fills gaps in `t()`).
  `<html lang>` syncs from `localeMeta(locale).htmlLang`.
- **`format.ts`** — `intlLocale` ternary replaced with `localeMeta(locale).intlLocale`.
- **`dateFnsLocale.ts`** — `locale === 'hi'` branch replaced with a
  `Partial<Record<Locale, DateFnsLocale>>` map (append one line per locale).
- **`LanguageSwitcher.tsx`** — renders `LOCALES.map(...)` instead of two literal
  buttons, so a new registry entry appears in the switcher automatically. With
  only en/hi registered the rendered output is identical to before.
- **`parity.test.ts`** — rewritten as a registry-driven pilot-coverage contract:
  `complete` locales require exact key parity + no blanks; `pilot` locales may be
  a subset but every defined key must exist in English, match its `{var}`
  placeholders, and be non-blank.
- **New `registry.test.ts`** — asserts every entry has non-empty metadata,
  unique codes, English is the default + complete, `localeMeta` round-trips and
  falls back, `isLocale` accepts only registered codes, and loaders exist for
  every non-English locale.

## Tests

- `npx tsc --noEmit` — clean
- `npx eslint src/shared/i18n/` — clean
- `npx vitest run src/shared/i18n/` — 29 passed (4 files), all pre-existing tests
  unedited
- `npm run build` — `hi-*.js` chunk splits out (75 kB), entry chunk 140 kB
  (under 160 kB budget)

## Next steps

LA-9b: register `mr` (Marathi) + backend `preferred_language` choice + a
`locales/mr.ts` pilot subset covering the anonymous journey. After 9a, that's a
one-line registry edit + a union widening + content.
