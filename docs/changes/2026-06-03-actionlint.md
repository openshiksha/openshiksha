# 2026-06-03 — actionlint workflow linting

## What

Added a `workflow-lint` job to `.github/workflows/ci-cd.yaml` that runs
[actionlint](https://github.com/rhysd/actionlint) against every workflow YAML
file in the repo.

## Why

`ci-cd.yaml` has grown to 9 jobs (~290 lines) with non-trivial constructs:
multi-`needs:` dependencies, branch-conditional `if:` expressions, an inline
`gh` shell script for sticky PR comments, several third-party actions pinned
to major-version tags. Mistakes in any of those — a typo in a `needs:` name, a
bad `${{ }}` expression, an action version that no longer exists — only
surface at run time, which is slow feedback when the workflow itself is the
thing being changed.

`actionlint` catches those statically in seconds. It's the standard tool
the GitHub Actions community uses for this and is the one the GitHub Actions
docs themselves recommend.

## How

- New `workflow-lint` job at the top of the jobs list.
- Installed via the official `download-actionlint.bash` script from the
  upstream repo — no third-party action dependency.
- `-shellcheck=` disables shellcheck integration. The inline `gh` script in
  the `Post coverage summary on PR` step is intentional shell, and chasing
  shellcheck style warnings is not the goal of this job; that can be added
  separately if we want it later.
- `-color` for readable output in the GitHub Actions log.

## Not done in this PR

- Did not add `actionlint` to the local pre-commit hook list. The hook would
  require contributors to have the binary installed (or use a Docker image),
  which is friction for a check that already runs in CI on every push.
- Did not enable shellcheck integration (see above).
