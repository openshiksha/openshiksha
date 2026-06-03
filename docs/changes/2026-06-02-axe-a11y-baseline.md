# 2026-06-02 — axe-core a11y baseline on /design

## What

Added an accessibility baseline Playwright spec (`frontend_modern/e2e/a11y.spec.ts`)
that runs axe-core against the `/design` showcase, writes a JSON summary to
`frontend_modern/axe-report/design.json`, and uploads it as a CI artifact
(`axe-report`) from the existing `frontend-e2e` job.

- New dev deps: `@axe-core/playwright`, `axe-core`.
- Spec is **non-blocking**: it always passes today and logs a summary to the
  test console. Toggle `FAIL_ON_BLOCKING = true` in the spec to gate on
  `serious` + `critical` violations once the WCAG 2.1 AA initiative starts.
- CI step: `Upload axe-core a11y report` (always-on, 14-day retention).

## Why

The V2 "Chalk & Unlock" design overhaul is the top active initiative, and
"Accessibility pass — WCAG 2.1 AA across the migrated V2 surfaces" is the
next-up backlog initiative. Standing up the measurement infra now lets the
design team see baseline a11y violations on the canonical showcase page as
new primitives land, so the eventual AA pass starts from data rather than
zero.

`/design` is the right anchor: it is the only public, backend-free route in
the app and the V2 DoD requires every primitive to be catalogued there.

## Baseline at landing time

axe-core (WCAG 2.0/2.1 A+AA tags) reports **2 violations** on `/design`:

- `color-contrast` (serious, 10 nodes) — largely intentional swatch examples.
- `label` (critical, 1 node) — `<input type="range">` inside the sandboxed
  thermo-piston widget iframe (M7-11 interactive widget content).

Both will be triaged when the AA initiative formally starts; until then the
artifact gives us a trend line.

## Out of scope

- Fixing the existing violations.
- Running axe on authenticated routes (would require the Docker stack).
- Gating CI on a11y findings.
