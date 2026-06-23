# 2026-06-22 — Visual-regression gating activated

**Classification:** Test infrastructure (activates existing, previously-skipped
framework).

## Summary
The Playwright visual-regression spec laid down in M6-03
([`2026-06-04-visual-regression.md`](2026-06-04-visual-regression.md)) was
`test.describe.skip`'d because no Linux baselines existed — Windows-generated
PNGs never match a Linux CI runner. This change generates the baselines, commits
them, un-skips the spec, and adds a dedicated CI job that runs the comparison
**inside the pinned Playwright Docker image** so the rendering environment is
identical to the one the baselines were generated in. Visual regressions now gate
`build-publish` (and therefore deploys), alongside the other `frontend-*` jobs.

## Why a container job (and not the bare runner)
Pixel-level screenshot comparison is only reproducible when the baseline and the
comparison run render in the same environment. A bare `ubuntu-latest` runner ships
a different system-font set than the Playwright image, so font anti-aliasing alone
would push diffs past tolerance and flake on every run. Running the job inside
`mcr.microsoft.com/playwright:v1.61.0-noble` — the same image used to generate the
baselines — removes that variable. Browsers are preinstalled in the image, so the
job skips `playwright install`, and the image tag is pinned to the
`@playwright/test` version in `package-lock.json` (**1.61.0**). Keep the two in
lockstep when bumping Playwright.

## Files changed
- `frontend_modern/e2e/visual.spec.ts` — removed `.skip`; tagged every test
  `@visual` so the bare-runner `frontend-e2e` job can exclude them.
- `frontend_modern/e2e/visual.spec.ts-snapshots/*-chromium-linux.png` — **new**,
  8 baselines (4 public surfaces × desktop/mobile), generated in the pinned image.
- `frontend_modern/package.json` — `test:e2e` now runs `--grep-invert @visual`
  (bare-runner job, no screenshots); new `test:e2e:visual` (`--grep @visual`);
  `test:e2e:update-snapshots` now scoped to `--grep @visual`.
- `.github/workflows/ci-cd.yaml` — new `visual-regression` job (runs in the
  Playwright container); added to `build-publish` `needs:`.

## How the snapshots were generated
On the host (Windows + Docker Desktop), from `frontend_modern/`:

```bash
docker run --rm -v "$PWD":/work -v /work/node_modules -w /work \
  mcr.microsoft.com/playwright:v1.61.0-noble \
  bash -lc "npm ci && npm run test:e2e:update-snapshots"
```

The anonymous `-v /work/node_modules` volume masks the host's `node_modules` so the
container installs Linux-native deps without clobbering the host. The generated
PNGs land on the bind mount under `e2e/visual.spec.ts-snapshots/`. Determinism was
confirmed by re-running `CI=true … npm run test:e2e:visual` (1 worker, 2 retries —
the exact CI settings) against the committed baselines: 8/8 passed.

## Refresh protocol (intentional design change)
When a design change legitimately alters one of the covered surfaces, regenerate
the affected baselines **in the same image** and commit them with the change:

```bash
cd frontend_modern
docker run --rm -v "$PWD":/work -v /work/node_modules -w /work \
  mcr.microsoft.com/playwright:v1.61.0-noble \
  bash -lc "npm ci && npm run test:e2e:update-snapshots"
git add e2e/visual.spec.ts-snapshots/
```

(On Git Bash, prefix with `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` so the
`/work` paths aren't mangled.) Never regenerate baselines on a non-Linux host or a
bare runner — the platform suffix and font rendering won't match CI.

## Scope (unchanged from M6-03)
Only **public, backend-free** routes are covered: `/design`, `/`, `/login`,
`/enquire`. Authenticated dashboards need the Docker stack + seeded DB and a
backend-attached Playwright project, which remains future work.
