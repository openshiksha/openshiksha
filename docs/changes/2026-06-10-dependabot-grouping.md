# 2026-06-10 — Group Dependabot version-update PRs

**Branch:** `infra/2026-06-10-dependabot-grouping` → `modernization`
**Type:** infra / CI hygiene

## What changed

Added `groups` to all three ecosystems in `.github/dependabot.yml`:

- **pip** (`/backend`) — `backend-minor-patch`: minor + patch version bumps
  land as one weekly PR.
- **npm** (`/frontend_modern`) — `frontend-minor-patch`: same, one weekly PR.
- **github-actions** — `github-actions`: all action pin bumps (majors
  included) land as one monthly PR.

Grouping applies to `version-updates` only:

- **Major** pip/npm bumps still open as individual PRs — they carry breaking
  changes and need real review in isolation.
- **Security updates** keep Dependabot's default one-PR-per-advisory
  behaviour, so they stay individually visible and fast to merge.
- Actions majors are batched into the monthly group because action pin bumps
  are low-risk and the `workflow-lint` (actionlint) job catches breakage.

## Why

The previous config opened up to 10 individual PRs per ecosystem per week.
Every PR triggers the full CI matrix — including the Playwright e2e job and
two coverage-gated test suites — so a routine Monday could burn a dozen CI
runs and a dozen review/merge round-trips on lockfile-level bumps. One
grouped PR per ecosystem gets the same updates with one CI run and one
review, while anything genuinely risky (majors, security advisories) still
arrives as its own PR.

## Notes for the dependabot routine

- A grouped PR that fails CI means *one of* the batched bumps broke
  something. Dependabot supports `@dependabot recreate` after excluding the
  offender via `ignore` if bisecting is needed.
- Open Dependabot alert count (74 as of today) is unaffected by this change —
  those are all against the deleted legacy `pip-requirements.txt` manifest
  and auto-resolve when the deletion reaches the default branch (`qa`). See
  [docs/infra/dependabot-legacy-stack.md](../infra/dependabot-legacy-stack.md).
