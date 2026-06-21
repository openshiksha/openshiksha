# Remove Marathi (मराठी) as a language option

**Date:** 2026-06-14
**Classification:** Improve (scope reduction)

## Summary

Remove Marathi from the language switcher. It shipped as a **pilot** locale
(LA-9) — a growing subset of keys with English filling the gaps — but coverage
stayed partial (e.g. the marketing home page and most teacher surfaces were never
translated), so a user who picked मराठी saw a mix of Marathi and English. Given
low usage and the inconsistent experience, English + Hindi (both `complete`
locales) are the supported set.

## What changed

- **`frontend_modern/src/shared/i18n/locales/registry.ts`** — `Locale` union
  narrowed to `'en' | 'hi'`; removed the `mr` lazy loader and the `mr` `LOCALES`
  entry. The `pilot` coverage model + `LocaleMeta` are kept so a future regional
  language can still ship surface-by-surface.
- **`frontend_modern/src/shared/i18n/locales/mr.ts`** — deleted.
- **`frontend_modern/src/shared/i18n/i18n.test.tsx`** — removed the Marathi-pilot
  describe block and the "selects Marathi" switcher test; the switcher now
  asserts exactly two buttons (`EN | हिं`).
- **`frontend_modern/src/shared/i18n/coverage.test.ts`** — emptied `PILOT_FLOORS`
  (no pilot locales remain) and routed the `coverage === 'pilot'` checks through a
  `LocaleMeta`-typed `isPilot` helper so the report stays generic for future
  pilots without tripping TS's narrowing.

## Technical details

- The switcher, parity guard, coverage report, date/number formatting and
  `<html lang>` sync are all registry-driven (LA-9a), so dropping `mr` is a
  registry edit — no consumer component changed.
- A previously-stored `preferred_language = 'mr'` is handled gracefully:
  `isLocale('mr')` now returns `false`, so `resolveInitialLocale` falls back to
  English (never a crash, never a blank).
- The lazy `mr` chunk is no longer emitted by the build.

## Tests

- `npx vitest run` — 411 passing (67 files); i18n suite green.
- `tsc --noEmit` clean, `npm run lint` clean, `npm run build` ok, bundle budget
  green (141.8 kB vs 160 kB); confirmed no `mr-*` chunk in `dist/`.

## Migration notes

Frontend-only. The backend may still *accept* `preferred_language = 'mr'` (it's a
harmless, now-unreachable value — the UI never sends it again). A follow-up could
drop `mr` from any backend language choices + migrate stored `mr` rows to `en`,
but that's out of scope for this UI change.

## Next steps

- Optional backend cleanup of the `mr` `preferred_language` choice + a data
  migration of existing `mr` rows → `en`.
