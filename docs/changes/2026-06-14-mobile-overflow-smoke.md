# Mobile-form-factor e2e smoke (Pixel 5) for public surfaces

**Classification:** New (test infrastructure).

## Summary
Add a Playwright smoke spec that exercises the public, backend-free routes —
`/`, `/login`, `/enquire`, `/design` — on an emulated handset (Pixel 5:
393×851, DPR 2.75, touch, mobile UA), and fails CI on the two cheapest,
highest-signal mobile regressions:

1. **Horizontal overflow** — `documentElement.scrollWidth` exceeding the layout
   viewport (with 1px slack). This is the single most common mobile layout bug
   and is invisible to the existing `Desktop Chrome`-only e2e project.
2. **Console / page errors** — a paint that throws only on mobile (a
   `matchMedia`/`ResizeObserver` path, etc.) that the desktop smoke would miss.

Directly supports the now-active **Mobile Shell & PWA-Offline** initiative
(docs/initiatives/2026-mobile-shell-pwa-offline.md): OpenShiksha targets K-12
students in India on phones, yet until now nothing in CI ran at phone width.

## Files changed
- **New** `frontend_modern/e2e/mobile.spec.ts` — 4 public routes, each asserting
  no horizontal overflow + no console errors at Pixel 5 emulation.

## Design notes
- Uses `test.use({ ...devices['Pixel 5'] })` at the file level rather than a
  second `playwright.config.ts` project, so it overrides only this spec's device
  instead of re-running every other spec (a11y, design, visual) at phone width.
- Runs under the existing `frontend-e2e` CI job + `vite preview` web server —
  **no CI YAML change** and no new dependency.
- Scope contract matches `visual.spec.ts`: public routes only. Authenticated
  mobile chrome (the M5-01 bottom tabs, the upcoming MSO-2 offline banner) needs
  the Docker stack + seeded DB and belongs in a future backend-attached project.

## Verification
Run locally (Windows, chromium): `npm run test:e2e -- mobile.spec.ts` — 4
passed. Type-check (`tsc --noEmit`) and ESLint both clean.
