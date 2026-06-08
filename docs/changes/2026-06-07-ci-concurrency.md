# 2026-06-07 — CI concurrency: cancel superseded runs on feature branches

## What

Added a top-level `concurrency:` block to `.github/workflows/ci-cd.yaml`:

```yaml
concurrency:
    group: ci-${{ github.ref }}
    cancel-in-progress: ${{ github.ref != 'refs/heads/modernization' && github.ref != 'refs/heads/qa' && github.ref != 'refs/heads/prod' }}
```

## Why

When developers push multiple commits in quick succession to the same PR
branch (typical when iterating on a review or fixing CI failures), every
push currently kicks off a fresh end-to-end run while the previous one is
still mid-flight. The older run's results are stale by the time it
finishes — we only care about the latest commit's verdict — so the wall
time and runner minutes spent on superseded runs are pure waste, and
they also push back the moment the latest commit's results land.

Grouping by `github.ref` and cancelling in-progress runs fixes that for
feature branches. The next push on the same ref cancels the previous run
and starts fresh on the new SHA.

## Why the deploy branches are excluded

`modernization`, `qa`, and `prod` runs trigger `build-publish` (push
Docker images to GHCR) and on `qa`/`prod` they also `deploy-*` (kubectl
apply + rollout). Cancelling those mid-flight could:

- leave a half-pushed image in GHCR (small, mostly cosmetic);
- start a rollout against an image SHA that the next run is about to
  replace, then race the next run's rollout against it.

For those branches each push runs to completion and the most recent
push's deploy is the one the cluster ends up on by ordering. The cost is
that two quick pushes to `qa` will burn ~2× the runner minutes — but
that's an unusual flow and the safety is worth it.

## Risk

Very low. Concurrency cancellation is a built-in GitHub Actions feature;
the syntax is exercised by `actionlint` in the existing `workflow-lint`
job. No application code is touched.
