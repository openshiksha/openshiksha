# Dependabot: cover Docker base images

**Date:** 2026-06-11
**Type:** infra
**Branch:** `infra/2026-06-11-dependabot-docker`

## What

Added two `docker` ecosystem entries to `.github/dependabot.yml`:

- `/backend` — `Dockerfile` + `Dockerfile.prod` (`python:3.11-slim`)
- `/frontend_modern` — `Dockerfile` + `Dockerfile.prod` (`node:20-alpine`
  builder stage, `nginx` runtime stage)

Both run monthly, target `modernization`, and group minor/patch bumps into a
single PR per directory. Majors (e.g. `python:3.11` → a new Python minor line,
which Docker tags treat as a major-ish runtime change) stay as individual PRs
because a base-runtime upgrade needs deliberate review against CI, mypy, and
the deploy images. Security updates keep Dependabot's default
one-PR-per-advisory behaviour.

## Why

Dependabot previously covered `pip`, `npm`, and `github-actions` — but the
deploy pipeline ships two production Docker images
(`backend/Dockerfile.prod`, `frontend_modern/Dockerfile.prod` → GHCR → k3s),
and nothing watched their base images. Base-image patch releases are how OS-level
CVE fixes (Debian slim, Alpine, nginx) reach the running pods; without this,
images only picked up fixes when someone rebuilt for an unrelated reason.

## Dependabot alert triage (same run)

All 3 open alerts (idna GHSA-65pc-fj4g-8rjx, urllib3 GHSA-qccp-gfcp-xxvc,
pillow GHSA-wjx4-4jcj-g98j) point at the deleted legacy `pip-requirements.txt`,
which still exists on the default branch `qa` (322 commits behind
`modernization`). Per `docs/infra/dependabot-legacy-stack.md` they auto-resolve
at the next `modernization → qa` promotion. The modern stack is clean: Pillow
is pinned at the patched 12.2.0, and idna/urllib3 are unpinned transitives that
resolve to patched versions (pip-audit in CI is green).
