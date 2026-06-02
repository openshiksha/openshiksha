# 2026-06-01 — Playwright e2e scaffold + `/design` smoke test

## What changed
- Added `frontend_modern/playwright.config.ts` (single chromium project, runs
  against `vite preview` on :4173 — no backend dependency).
- Added `frontend_modern/e2e/design.spec.ts`: smoke test that visits `/design`,
  asserts the page returns 2xx, an `h1` renders, the `#FF6F00` brand-token
  swatch is visible, and the browser console reports zero errors.
- Added new CI job `frontend-e2e` to `.github/workflows/ci-cd.yaml`; gated
  `build-publish` on it so a red e2e blocks deploy.
- Updated `.gitignore` to exclude `test-results/`, `playwright-report/`, and
  the playwright browser cache under `frontend_modern/`.

## Why
The V2 "Chalk & Unlock" design overhaul
(`docs/initiatives/2026-design-system-v2.md`) requires every new primitive to
land in the `/design` showcase. Until now there was no automated check that
the showcase still rendered after a refactor — a broken token, a typo in a
seed component, or a missing import would only surface when a human opened
the page locally. The smoke test gives CI a single, fast signal that "the
design system page still mounts and the brand token is on screen."

The `@playwright/test` dep was already in `package.json` and the `test:e2e`
script was already defined, but neither a config file nor any tests existed —
this PR fills in the scaffold so future visual-regression / per-page smoke
tests can be added in the same shape.

## Scope notes
- Single browser (chromium) — kept narrow on purpose; expand only when a
  bug is found that needs cross-browser coverage.
- No backend in the loop. When we add tests that hit Django, run them as a
  separate Playwright `project` here and gate the matching CI job on a
  Docker compose stack — do not bolt backend startup into this job.
- Visual-regression (Playwright `toHaveScreenshot`) is intentionally NOT
  enabled yet: font rendering on Linux CI differs from the Windows/macOS
  workstations where baselines would be generated, and managing that drift
  is its own initiative. Smoke first; pixel diffing later.
