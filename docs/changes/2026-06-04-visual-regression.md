# M6-03 — Visual-regression screenshot set

**Classification:** New (test infrastructure).

## Summary
Lay down the Playwright visual-regression test framework over the V2 public
surfaces — `/design`, `/`, `/login`, `/enquire` — at both desktop (1280×800)
and mobile (375×720) viewports. The spec is **skipped by default** until
Linux baselines have been generated and committed on CI (Windows-generated
PNGs would never match a Linux CI runner). The infra is in place; activation
is a documented one-step follow-up.

## Files changed
- **New** `frontend_modern/e2e/visual.spec.ts` — 4 surfaces × 2 viewports = 8
  Playwright snapshots, gated by `test.describe.skip` until baselines exist.
- `frontend_modern/package.json` — adds `test:e2e:update-snapshots` script
  for regenerating baselines after an intentional design change.

## How activation works
1. On the **Linux** runner (or the existing CI `frontend-e2e` job), check
   out this branch and run:
   ```bash
   cd frontend_modern
   npm ci
   npx playwright install --with-deps chromium
   npm run test:e2e:update-snapshots -- visual.spec.ts
   ```
2. Commit the generated PNGs under
   `frontend_modern/e2e/visual.spec.ts-snapshots/` (suffix
   `-chromium-linux.png`).
3. Remove the `.skip` from `test.describe.skip` in `visual.spec.ts` in the
   same commit. CI is now gating.
4. Subsequent intentional design changes: re-run
   `npm run test:e2e:update-snapshots` and commit the updated PNGs alongside
   the design change PR.

## Why "public, backend-free" surfaces only
The existing `playwright.config.ts` runs against `vite preview` — no Django
backend is booted. Authenticated dashboards (Student, Teacher, Parent, Admin,
Profile, Proficiency, …) require the Docker stack + seeded DB and belong in
a separate `playwright` project (gated on a Docker compose job). That's a
M6-03 follow-up; the four public surfaces here are the immediate value
since they're the first impression every parent / prospective school sees.

## Design choices
- **Both viewports.** Mobile (375) catches the regressions the eye misses on
  the dev laptop — exactly the layouts BottomNav (#195) and Navbar polish
  (#198) most influenced. Desktop captures the showcase rhythm.
- **`maxDiffPixelRatio: 0.02`.** Generous enough to absorb sub-pixel font
  anti-aliasing between Linux kernels / Playwright versions; tight enough to
  catch a real layout regression.
- **Waits on `document.fonts.ready`** before snapshotting — Fraunces +
  Inter load over the network in CI and would otherwise shift character
  widths mid-paint.
- **Wait on the page's `h1`** rather than `networkidle` — `/design` and the
  marketing surfaces don't fire any network after initial paint, so
  `networkidle` would hang.

## What this does *not* cover (yet)
- **Authenticated surfaces** — dashboards, Profile, Proficiency, Assignment
  detail, SRS drill, Browse-Practice, Question Bank, CreateQuestion, the
  Teacher panels. Needs the Docker stack + a `playwright` project that
  authenticates as a demo user.
- **`/register`, `/register/school`, `/register/open`** — also public but
  share the chalkboard/paper `AuthLayout` already covered by `/login`. Adding
  them is a one-line change once baselines are seeded.
- **A11y regression coverage** — that's the existing `a11y.spec.ts` over
  axe-core; this PR is purely visual.

## Verification
- `npm run type-check`, `npm run lint` — green.
- `npx playwright test --list` — confirms the 8 snapshot test cases are
  registered (and currently skipped).

## Next
M7-04 legacy feature-parity audit.
