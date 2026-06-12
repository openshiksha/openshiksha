# LA-1 — i18n foundation, language switcher, auth-pages pilot

**Date:** 2026-06-11
**Classification:** New
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-1)

## Summary

First increment of the Language Access initiative: a tiny in-house i18n module
(`frontend_modern/src/shared/i18n/`), an "EN | हिं" language switcher in the
navbar / mobile account sheet / auth pages, and the login surface migrated to
translation keys with real Hindi strings. One tap switches the login page to
Hindi; the choice persists per device via `localStorage('os_lang')`.

## Legacy files referenced

None portable — the legacy Django 1.11 platform was English-only (no
`USE_I18N`, hardcoded template strings). This is pure "Improve": the modern
SPA centralizes strings, so i18n becomes feasible at all.

## What changed and why

- **`src/shared/i18n/locales/en.ts`** — flat `Record<key, string>` dictionary;
  `LocaleKey` is derived from it so typo'd keys are type errors.
- **`src/shared/i18n/locales/hi.ts`** — Hindi dictionary typed `LocaleDict =
  Record<LocaleKey, string>`, so key parity with English is **tsc-enforced**
  (runtime parity test lands in LA-5). Loaded with a dynamic `import()` —
  it builds as its own chunk (`hi-*.js`), keeping the entry chunk flat.
- **`i18nContext.ts` + `I18nProvider.tsx` + `useT.ts`** — context provider with
  `locale`/`setLocale`/`t()`. `{var}` interpolation; English fallback while the
  Hindi chunk loads or if a key drifts (dev-mode `console.warn`); persists to
  localStorage; syncs `<html lang>`. Without a provider the context degrades to
  a working English-only translator (keeps isolated component tests
  wrapper-free). **No i18next** — initiative principle 2 (perf budget).
- **`LanguageSwitcher.tsx`** — compact segmented EN/हिं toggle, `aria-pressed` +
  per-button `aria-label`, V2 tokens.
- **Wiring:** `I18nProvider` wraps the router in `App.tsx`; switcher added to
  `Navbar` (desktop right cluster), the mobile account sheet, `LoginPage`, and
  `AuthLayout`.
- **Pilot migration:** `LoginPage.tsx` + `AuthLayout.tsx` strings moved to
  `t()` keys with real Hindi values per the initiative Glossary.
- **Fonts:** `Noto Sans Devanagari` added to the Google Fonts request and to
  the Tailwind `sans`/`display` stacks behind Inter/Fraunces. Google Fonts
  serves it with `unicode-range`, so the binary only downloads when Devanagari
  glyphs actually render — zero cost for English-only sessions.

## Technical details

- Entry chunk after change: **96.55 kB** (budget 160 kB; was ~93 kB — the en
  dictionary + provider cost ~3.5 kB). Hindi dict is a separate lazy chunk.
- Boot locale precedence (`resolveInitialLocale`): localStorage > `'en'`.
  LA-2 inserts the profile `preferred_language` layer between the two.
- Devanagari rendering verified in a real browser:
  [screenshot](../initiatives/screenshots/2026-06-11-la1-login-hindi.png).

## Tests

- New `src/shared/i18n/i18n.test.tsx` (7 cases): default English, `{var}`
  interpolation, switch-to-Hindi + persistence + `<html lang>` sync,
  English-fallback-never-blank, `resolveInitialLocale` precedence/validation,
  provider-less fallback, switcher `aria-pressed` toggling.
- `LoginPage.test.tsx` extended: renders in Hindi via `initialLocale="hi"`,
  switches to Hindi via the toggle.
- Full suite: 53 files / 336 tests green; lint + tsc clean; build + bundle
  budget green.

## Migration notes

None (frontend only).

## Next steps

LA-2 (`User.preferred_language` end-to-end), LA-3 (student chrome), LA-4 (AI
content language), LA-5 (runtime parity guard + parent/registration chrome).
