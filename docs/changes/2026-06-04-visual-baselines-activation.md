# M6-03 — Visual-regression baseline activation

**Classification:** New (CI infrastructure).

## Summary
Adds a manual GitHub Actions workflow that seeds the Linux Playwright
baselines for `e2e/visual.spec.ts` (M6-03 / #203). The visual-regression
infra has been in the repo since #203 but skipped, because Linux baselines
need to be generated on a Linux runner. This workflow makes activation a
single-click operation in the GitHub Actions tab.

## Files changed
- **New** `.github/workflows/seed-visual-baselines.yaml` — `workflow_dispatch`
  job that:
  1. Checks out the chosen branch (default: the branch the workflow is
     dispatched from).
  2. Installs Node, Playwright chromium, dependencies.
  3. If `visual.spec.ts` still has `test.describe.skip`, swaps it for
     `test.describe` (one-time activation).
  4. Runs `npx playwright test visual.spec.ts --update-snapshots`, writing
     PNGs to `e2e/visual.spec.ts-snapshots/`.
  5. Commits and pushes the baselines back to the target branch (only if
     anything actually changed).

## How to use

### First-time activation (one-shot)
1. Open the **Actions** tab → **Seed visual-regression baselines** →
   **Run workflow**.
2. Pick `modernization` (or any branch you want the baselines committed to).
3. Wait ~2 min. The workflow auto-commits a `ci(visual): refresh Linux
   Playwright baselines` commit containing the eight `*-chromium-linux.png`
   files **and** the `.skip` removal.
4. From this point on the visual spec runs in the regular `frontend-e2e` CI
   job and fails the build on any pixel diff above the configured
   `maxDiffPixelRatio: 0.02` threshold.

### Refreshing after an intentional design change
1. Land your design PR on a branch.
2. Open the workflow against that branch.
3. The workflow re-runs `--update-snapshots`, refreshing the existing PNGs
   in place; commits + pushes.
4. The PR diff now includes the visual changes for review.

## Why a separate workflow (not the main CI job)
- The main `frontend-e2e` job runs on every PR — it should *gate* on the
  baselines, not regenerate them. Otherwise a real visual regression would
  silently overwrite the reference instead of failing the build.
- Separation also means `--update-snapshots` only ever runs when a human
  explicitly asks for it (via Actions UI), which is the right safety
  posture for "this change is intentional, commit the new baseline".

## Verification
- Workflow YAML linted via the standard YAML parser (no `yamllint` in
  pipeline; the syntax mirrors the existing `ci-cd.yaml` blocks).
- Manual confirmation pending the first `workflow_dispatch` run.

## Closes M6-03
With this PR the visual-regression initiative item moves from `~` to `x` in
the V2 ledger: the scaffold ships in #203, activation ships here. Recurring
baseline maintenance is now a one-click op.

## Next
This was the last of the three V2 follow-ups (along with `ADMINS` env
wiring #205 and the QuestionBank chapter filter #206). The V2 "Chalk &
Unlock" initiative's backlog is now `[x]` end-to-end except for explicitly
deferred non-goals (full keyboard walkthrough / screen-reader spot-check /
axe-core CI gating / authenticated-surface visual snapshots), each of which
is documented in the backlog with the right owning future initiative.
