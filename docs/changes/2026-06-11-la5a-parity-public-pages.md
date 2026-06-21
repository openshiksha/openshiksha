# LA-5a — key-parity guard + public pages (home + registration) in Hindi

**Date:** 2026-06-11
**Classification:** Improve / hardening
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-5, first half)

## Summary

Two things: (1) the runtime key-parity guard that keeps the two locale files
from drifting, and (2) the whole public surface — the marketing home page and
all three registration pages — now renders in Hindi. With LA-1 (login) this
makes the entire anonymous-visitor journey bilingual. The home page also gets
the language switcher in its top bar. (Home page added to LA-5 scope per user
request mid-run; parent-dashboard chrome + glossary/ledger docs follow as
LA-5b.)

## Legacy files referenced

None — legacy was English-only.

## What changed and why

- **`src/shared/i18n/parity.test.ts`** — Vitest guard, zero CI pipeline
  changes (runs in the existing vitest gate). Three checks: identical key
  sets (fails listing the drifted keys), no blank strings, and — what tsc
  cannot enforce — `{var}` interpolation placeholders match between locales.
- **`HomePage.tsx`** — all copy through `t()` (~40 `home.*` keys); pillar and
  feature arrays now carry `LocaleKey`s; the bolded "Open Model" /
  "Partnership Model" sentence is composed from pre/term/post keys so the
  emphasis survives translation; `LanguageSwitcher` added to the top bar.
- **`RegisterPage` / `RegisterOpenPage` / `RegisterSchoolPage`** — labels,
  buttons, descriptions, and the client-side error fallback through `t()`
  (~25 `register.*` keys). `extractError` keeps server messages verbatim —
  server-side message localization is deliberately LA-7 scope.

## Tests

- New `parity.test.ts` (3 cases) — red→green verified by temporarily removing
  a hi key (fails naming the key) and restoring it.
- New `HomePage.test.tsx` (English default + full-Hindi render).
- Full suite 56 files / 353 tests green; lint/tsc/build/budget green
  (entry 103.72 kB of 160 kB — home keys are eager because HomePage is on the
  first-paint path; Hindi stays lazy).
- Visual: [home page in Hindi](../initiatives/screenshots/2026-06-11-la5-home-hindi.jpg).

## Migration notes

None (frontend only).

## Next steps

LA-5b: parent dashboard chrome + glossary/ledger/STATUS/ROADMAP updates.
