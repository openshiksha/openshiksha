# 2026-06-18 — CI: least-privilege GITHUB_TOKEN floor on ci-cd.yaml

## What

Added a top-level `permissions:` block to `.github/workflows/ci-cd.yaml`:

```yaml
permissions:
    contents: read
```

This sets the default `GITHUB_TOKEN` scope for every job in the workflow to
read-only on repository contents. The two jobs that need more already declare
their own (overriding) block and are unchanged:

- `test` → `contents: read` + `pull-requests: write` (posts the coverage comment)
- `build-publish` → `contents: read` + `packages: write` (pushes images to GHCR)

The other nine jobs (`workflow-lint`, `lint`, `typecheck`, `security`,
`frontend`, `frontend-e2e`, `lighthouse`, `deploy-qa`, `deploy-prod`) only
check out the repo and run tools/manifests, so `contents: read` is sufficient.

## Why

Without an explicit `permissions:` block, a workflow inherits the
repository/organization default token scope. On older repos that default is
**read/write all** — a token far more powerful than any of these jobs need. If
a build step (or a transitively-pulled dependency / action) were compromised,
that broad token could push commits, edit issues/PRs, or alter releases.

Setting an explicit least-privilege floor is the GitHub-recommended hardening
and is the convention the repo already follows on its newer workflows
(`dependabot-automerge.yaml`, `dependency-review.yaml` both set top-level
`permissions:`). This change brings the main pipeline in line with them.
`codeql.yaml` was intentionally left as-is: its single `analyze` job already
declares an explicit job-level block, so a top-level floor would be redundant.

## Risk

Very low. No application code is touched, and no job loses a permission it
relies on — the only two jobs that need elevated scopes already grant them to
themselves, and per-job `permissions:` fully override the top-level block
rather than merging with it. The change is validated by the existing
`workflow-lint` (actionlint) job. The worst realistic failure mode would be a
job that silently needed a scope it no longer has; that would surface as a
clear 403 in the affected step, not as a hard-to-diagnose data issue.
