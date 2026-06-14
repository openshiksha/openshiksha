# LA-9e — Marathi glossary + coverage report + LA-9 close-out

**Date:** 2026-06-13
**Classification:** Hardening / docs — closes LA-9
**Initiative:** Language Access — depends on LA-9a (#349); reports on 9b–9d

## Summary

Closes the LA-9 third-language pilot: adds a **pilot-coverage report** test, a
**Marathi glossary** section, and flips the initiative + STATUS board to reflect
that the i18n framework is proven for N languages.

## What changed

- **New `frontend_modern/src/shared/i18n/coverage.test.ts`** — for each `pilot`
  locale, logs `<code> (<nativeName>): N/<total> keys (<pct>%)` so a reviewer
  sees coverage at a glance (Marathi currently **137/764 = 17.9%** — the
  anonymous journey + student loop + parent dashboard). Asserts a per-locale
  floor (`mr ≥ 45`) so coverage can't silently regress below the LA-9b baseline.
  `complete` locales are covered by parity.test.ts and skipped.
- **`docs/initiatives/2026-language-access.md`** — added a Marathi glossary
  section (flagged for human review), appended ledger rows for 9a–9e, flipped
  the **LA-9 backlog row to ✅**, and updated the title/status to include मराठी.
- **`docs/initiatives/STATUS.md`** — headline now reads "LA-9 shipped — the
  third language (Marathi) pilot proves the framework; only LA-10 (blocked on
  product design) remains"; priority-table row updated; Mobile shell / PWA-offline
  named as the next seed.

## Tests

- `vitest run src/shared/i18n/` → 41 passed (5 files, incl. the new coverage
  report). `tsc`/`eslint` clean.

## Outcome

The North Star clause — "a third language must be a content task, not an
engineering task" — is met: the entire engineering surface for Marathi was one
`LOCALES` registry entry + a `Locale` union widening (LA-9a/9b); everything else
was content. Language #4 (a non-Devanagari stress test like Tamil) is now
config + content + one font-stack entry, no code change. Only **LA-10**
(authored-content/question translation) remains on Language Access and stays
**blocked on product design**.
