# Contributing to OpenShiksha

Thanks for your interest in improving OpenShiksha! This guide covers how to get
set up, the branch model, and the conventions CI enforces.

## Getting set up

See the [Quickstart in the README](README.md#quickstart-local) and
[`docs/dev/local-development.md`](docs/dev/local-development.md) for the full local environment
(Docker Compose for backend + Postgres + Redis + Celery, Vite for the frontend).

Install the pre-commit hooks once — they run `black`, `isort`, `flake8`, and
basic hygiene checks on every commit:

```bash
pip install pre-commit
pre-commit install
```

## Branch model

```
feature/*  ──PR──▶  qa  ──(CI builds + auto-deploys)──▶  production
```

- Branch off **`qa`** and open your PR **against `qa`**. `qa` is the trunk — all
  feature work integrates here.
- A merge to `qa` is a release: CI builds the images and deploys to production
  automatically, so keep `qa` green and review every PR before merging.
- Use descriptive branch names: `feat/...`, `fix/...`, `docs/...`, `chore/...`.

See [`docs/dev/git-strategy.md`](docs/dev/git-strategy.md) for the full rationale.

## Commit & PR conventions

- **Conventional-commit style** subjects: `feat(scope): …`, `fix(scope): …`,
  `docs: …`, `chore: …`, `ci: …`.
- Keep each PR **focused and reviewable** — one concern per PR. Split large
  mechanical changes (e.g. file moves) from behavioural ones.
- Write a clear PR description: what changed and why. Link any related issue or
  initiative (`docs/initiatives/`).

## Tests & checks (run before pushing)

CI gates every push; you can run the same checks locally:

```bash
# Backend
cd backend
black --check --line-length=120 openshiksha/
isort --check --profile=black --line-length=120 openshiksha/
flake8 openshiksha/
mypy openshiksha/
pytest

# Frontend
cd frontend_modern
npm run lint
npx tsc --noEmit
npm test
npm run build
```

All of these must pass for a PR to merge. New behaviour should come with tests.

## Ways to contribute content & widgets

Beyond code fixes, there are two purpose-built contribution funnels — one for
*data*, one for *code*:

- **Question content → [content packs](contrib/packs/README.md).** A content
  pack is a schema-validated JSON bundle of questions (optionally using
  existing interactive widgets). CI validates your pack on the PR; after merge
  a maintainer stages it and **approves it in-app** before anything reaches the
  question bank — published with the attribution from your pack's provenance
  block. No Python/TypeScript needed.
- **New interactive widgets → normal code review.** Widgets are code and ship
  **only** via pull-request review — never through the content pipeline. Start
  with a [widget proposal issue](.github/ISSUE_TEMPLATE/widget_proposal.md) to
  agree on scope, build with the [SDK guide](docs/widgets/anatomy.md), and
  clear the [review bar](docs/widgets/review-bar.md) (sandbox rules, schema
  parity, tests, accessibility).

## Reporting bugs & requesting features

Open a GitHub issue with clear reproduction steps (for bugs) or the problem you're
trying to solve (for features). For **security issues**, do **not** open a public
issue — follow [`SECURITY.md`](SECURITY.md).

## Code of conduct

By participating you agree to uphold our
[Code of Conduct](CODE_OF_CONDUCT.md). Be kind and constructive.
