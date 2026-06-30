# Retarget contributor branch-model docs from deleted `modernization` to the `qa` trunk

**Date:** 2026-06-29
**Type:** docs / infra hygiene

## Problem

The `modernization` branch was squash-merged into `qa` and **deleted** when the
modern stack became the trunk, but the contributor-facing documentation still
told people to branch off and PR against `modernization`. For a repo on the
open-source-readiness track, that is broken onboarding: a new contributor
following `CONTRIBUTING.md` or the README would target a branch that no longer
exists, and a repo admin following `docs/infra/branch-protection.md` would try to
protect a non-existent branch.

This continues the dead-branch cleanup started in #440 (which repointed the
Dependabot/CI *triggers* from `modernization` to `qa`) — that PR fixed the
machinery; this one fixes the human-facing docs.

## What changed (docs only — no code or CI behaviour)

- **`CONTRIBUTING.md`** — branch-model diagram + instructions now say *branch off
  `qa`, PR against `qa`*, and explain that a merge to `qa` is an auto-deploying
  release.
- **`README.md`** — "Branch → environment model" section corrected to the
  single-trunk `feature/* → qa → production` flow.
- **`docs/dev/git-strategy.md`** — rewritten. The old file was the original
  migration-era plan (legacy Python 2.7 on `main`, modern work on
  `modernization`, a "Migration to Production" cut-over, `frontend/` paths). All
  of that is complete and obsolete. The new version documents the current
  trunk-based model, the feature workflow, the PR process, and a short history
  note pointing at `setup-modernization.md` and `legacy/`.
- **`docs/dev/README.md`** — the one-line branch-model summary updated.
- **`docs/infra/branch-protection.md`** — now protects the single `qa` trunk
  (was: `modernization` + `qa`); verification `gh api` snippet updated.

## Out of scope (intentionally left)

- The `deploy-qa` job in `ci-cd.yaml` still gates on `refs/heads/modernization`,
  but its own comment documents it as a disabled future-state sketch (also
  double-gated behind the unset `QA_ENV_ENABLED` variable), so it never runs.
  Left as-is to keep this change docs-only and atomic.
- Historical references in `docs/changes/`, `docs/daily-plans/`,
  `docs/deploy/README.md`, and `frontend_modern/README.md` are dated record /
  narrative, not live branch guidance — preserved as history.
