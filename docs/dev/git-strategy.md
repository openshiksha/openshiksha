# OpenShiksha — Git Branching Strategy

## Overview

OpenShiksha uses a simple **trunk-based** model. All feature work integrates into
a single long-lived branch, **`qa`**, which is also the release branch: a merge to
`qa` builds the production images and deploys them automatically (see
[`.github/workflows/ci-cd.yaml`](../../.github/workflows/ci-cd.yaml)).

> **History.** The codebase was rebuilt from a legacy Django 1.11 / Python 2.7
> monolith onto Django 4.2 + React 18. That rebuild happened on a dedicated
> `modernization` branch, which was squash-merged into `qa` and **deleted** once
> the modern stack became the trunk. The retired monolith now lives under
> [`legacy/`](../../legacy/) for reference. See
> [setup-modernization.md](setup-modernization.md) for how the modern stack was
> bootstrapped. **Do not branch from or PR against `modernization` — it no longer
> exists.**

## Branch structure

```
qa (trunk + release — Django 4.2 / Python 3.12 + React 18)
 │   merge here ⇒ CI builds images + auto-deploys to production
 │
 ├── feat/...     feature work
 ├── fix/...      bug fixes
 ├── docs/...     documentation
 ├── chore/...    tooling / housekeeping
 └── infra/...    CI / infrastructure
```

- **`qa`** (protected) — the trunk. Every change lands here via PR. A merge is a
  release, so it stays green and reviewed at all times.
- **`prod`** — when pushed, CI also builds images tagged `prod`, but the live
  cluster is currently rolled out from `qa` (the `deploy-prod` job triggers on
  `qa`). Treat `prod` as a future-state release-train branch, not part of the
  day-to-day flow.

## Feature workflow

```bash
# Always start from an up-to-date trunk
git checkout qa
git pull origin qa

# Create a descriptive feature branch
git checkout -b feat/short-description

# ...work, commit (pre-commit hooks run black/isort/flake8)...
git push -u origin feat/short-description

# Open a PR on GitHub: feat/short-description → qa
```

Keep a branch up to date with the trunk before merge:

```bash
git checkout feat/short-description
git pull origin qa        # or: git merge qa
# resolve conflicts, push
```

## Pull request process

1. **Open a PR** from your feature branch → `qa`.
2. **CI runs automatically** (lint, type-check, security audit, backend + frontend
   tests, e2e, visual regression, k8s/alerting manifest validation).
3. **Get a review** — at least one approval (see branch protection below).
4. **Merge** once CI is green and the conversation is resolved.
5. **Delete** the feature branch.

One concern per PR — split mechanical changes (e.g. file moves) from behavioural
ones so reviews stay tractable. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for
commit/PR conventions.

## Branch protection

`qa` should be protected: require a PR + 1 approval, require passing status checks,
and disallow force-pushes and deletion. The full recommended GitHub configuration
is documented in
[`docs/infra/branch-protection.md`](../infra/branch-protection.md).

## Rules of thumb

### ✅ DO
- Branch off `qa` and PR back into `qa`.
- Use the `feat/` `fix/` `docs/` `chore/` `infra/` prefixes.
- Keep `qa` releasable — it deploys to production on merge.
- Write clear, conventional-commit messages.

### ❌ DON'T
- **Don't** branch from or target `modernization` (deleted).
- **Don't** commit directly to `qa` — always go through a PR.
- **Don't** force-push or delete protected branches.
- **Don't** edit retired code under `legacy/` as part of feature work.
