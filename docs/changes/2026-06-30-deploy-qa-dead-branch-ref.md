# Retarget the `deploy-qa` CI job off the deleted `modernization` branch

**Date:** 2026-06-30
**Type:** infra hygiene / drift-safety (CI)

## Problem

The `modernization` branch was squash-merged into `qa` and **deleted** when the
modern stack became the trunk. The dead-branch cleanup done in
[#440](https://github.com/openshiksha/openshiksha/pull/440) (CI/Dependabot
*triggers*) and [#487](https://github.com/openshiksha/openshiksha/pull/487)
(contributor docs) left one known reference behind: the `deploy-qa` job in
`ci-cd.yaml` still gated on `refs/heads/modernization`.

```yaml
if: github.ref == 'refs/heads/modernization' && vars.QA_ENV_ENABLED == 'true'
```

`#487` deferred it on purpose to keep that change docs-only and atomic (see its
"Out of scope" note). It is harmless today — the job is double-gated behind the
unset `QA_ENV_ENABLED` variable, so it never runs — but the condition references
a branch that can never exist again, which reads as broken to anyone who tries to
activate it. This closes that last `modernization` reference in `.github/`.

## What changed

- **`.github/workflows/ci-cd.yaml`** — the `deploy-qa` trigger no longer
  hard-codes a branch name. Activation is now config-driven via a new
  `QA_ENV_BRANCH` repo variable:

  ```yaml
  if: github.ref == format('refs/heads/{0}', vars.QA_ENV_BRANCH) && vars.QA_ENV_ENABLED == 'true'
  ```

  The surrounding comment block is rewritten to document the three-step
  activation (provision a qa cluster + secret → set `QA_ENV_BRANCH` → set
  `QA_ENV_ENABLED=true`).
- **`README.md`** — the branch-model note now mentions the `QA_ENV_BRANCH`
  variable alongside `QA_ENV_ENABLED`.

## Behaviour (unchanged — the job still never runs)

Both `QA_ENV_BRANCH` and `QA_ENV_ENABLED` are unset in the repo. With
`QA_ENV_BRANCH` unset, `format('refs/heads/{0}', '')` renders `refs/heads/`,
which is never a real ref, so the branch comparison can never be true — and
`QA_ENV_ENABLED` remains a second independent gate. The job is exactly as
disabled as before, now without naming a deleted branch. No other job depends on
`deploy-qa` (`build-publish`/`deploy-prod` do not `needs:` it), so nothing else
is affected. `actionlint` validates the workflow in the `workflow-lint` job.

## Why not delete the job instead

`README.md` and `docs/deploy/README.md` both cite `deploy-qa` as the reference
wiring for a future dedicated qa cluster. Repairing it (rather than deleting it)
preserves that documented scaffolding while removing the drift.
