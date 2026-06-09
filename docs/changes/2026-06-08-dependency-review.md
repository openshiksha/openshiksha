# Dependency Review on PRs — 2026-06-08

## What

New workflow `.github/workflows/dependency-review.yaml` runs
[`actions/dependency-review-action@v4`](https://github.com/actions/dependency-review-action)
on every PR targeting `modernization`, `qa`, or `prod`. It diffs the PR's
dependency manifests against the base branch and fails when a PR introduces
a package with a **high** (or higher) severity CVE.

## Why

The existing `security` (pip-audit) and `frontend` (npm audit) jobs in
`ci-cd.yaml` audit the *current committed* lockfile on every push. They will
eventually catch a newly-introduced vulnerable package, but only *after* it
has merged to `modernization`. Dependency Review gates the diff at PR time so
the bad version never lands.

This is especially valuable for Dependabot PRs: if Dependabot proposes a
bump that itself introduces a new transitive CVE (rare but possible),
the bump fails review instead of getting auto-merged or rubber-stamped.

## Why a separate workflow file

`ci-cd.yaml` is `on: push`. `actions/dependency-review-action` requires the
`pull_request` event (it needs `base.sha` to diff against). Splitting it out
keeps the existing push-triggered pipeline untouched and avoids dual-triggering
the heavy `test` / `frontend-e2e` jobs on both `push` and `pull_request`.

## Allowlist

- `GHSA-grgv-6hw6-v9g4` (twisted) — matches the ignore in the `security` job;
  fix only in 26.4.0rc2 (pre-release). Re-evaluate when twisted 26.4.0 stable
  ships.
- `PYSEC-2025-183` (pyjwt) — no GHSA mapping, so it isn't matched by the
  action's GHSA-only allowlist. The disputed advisory is still covered by
  `pip-audit` in `ci-cd.yaml`.

## Verification

- `actionlint` job in `ci-cd.yaml` will validate the new YAML's syntax on this
  PR.
- The workflow itself can only be exercised against a real PR; this change
  *is* the first such PR.
