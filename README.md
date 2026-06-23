<div align="center">

# OpenShiksha

**Free, adaptive learning and educational analytics for K–12 Maths & Science.**

Built for students, and for the teachers, parents, and schools who guide them.
CBSE · Classes 7–10 · English & हिन्दी.

[![CI/CD](https://github.com/openshiksha/openshiksha/workflows/CI/CD%20Pipeline/badge.svg?branch=qa)](https://github.com/openshiksha/openshiksha/actions)
[![CodeQL](https://github.com/openshiksha/openshiksha/workflows/CodeQL/badge.svg)](https://github.com/openshiksha/openshiksha/actions)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-brightgreen)](LICENSE.md)

🌐 **[openshiksha.org](https://openshiksha.org)**

</div>

---

## What it is

OpenShiksha is a production ed-tech platform: students practise auto-graded
Maths & Science questions with LaTeX-rendered, variable-randomised content;
teachers author assignments and watch class analytics; parents follow progress;
and an AI layer (Gemini / Claude) generates explanations, diagnoses
misconceptions, and drafts content. It is fully internationalised (English /
Hindi / Marathi) and accessible (WCAG 2.1 AA in progress).

## Architecture

```
                      ┌────────────────── Traefik (k3s ingress) ──────────────────┐
   browser ── HTTPS ──┤  /api/* /admin/* /static/*  →  backend (Django + Daphne)  │
                      │  everything else            →  frontend (React SPA, nginx) │
                      └───────────────────────────────────────────────────────────┘
                                      │                        │
                          ┌───────────┴──────────┐             │
                          │  PostgreSQL (data)    │     Celery worker + beat
                          │  Redis (cache/broker) │     (async grading, AI tasks)
                          └───────────────────────┘
```

| Layer        | Tech                                                                 |
| ------------ | -------------------------------------------------------------------- |
| **Backend**  | Django 6 · Python 3.12 · Django REST Framework · Daphne (ASGI/WebSockets) |
| **Frontend** | React 18 · TypeScript · Vite · Tailwind                              |
| **Data**     | PostgreSQL 15 · Redis 7                                              |
| **Async**    | Celery (worker + beat)                                               |
| **AI**       | Google Gemini / Anthropic Claude (pluggable, with Ollama fallback)  |
| **Infra**    | Docker · Kubernetes (k3s) · kustomize · Traefik · cert-manager      |
| **CI/CD**    | GitHub Actions → GHCR → k3s                                          |

## Repository layout

```
backend/          Django 6 backend (the API, admin, async tasks, AI)
frontend_modern/  React 18 + Vite single-page app
k8s/              Kubernetes manifests (kustomize: base + qa/prod overlays)
docs/             Architecture, deploy, initiatives, change logs
.github/          CI/CD workflows
legacy/           Retired Python 2.7 / Django 1.11 monolith — archived, not built
```

## Quickstart (local)

Requires Docker + Docker Compose, and Node 20 for the frontend dev server.

```bash
git clone https://github.com/openshiksha/openshiksha.git
cd openshiksha
cp backend/.env.example backend/.env          # fill in values (a Google AI key is optional)

# Backend + Postgres + Redis + Celery
docker compose up

# Frontend dev server (separate terminal)
cd frontend_modern && npm install && npm run dev
```

Then seed demo content:

```bash
docker compose exec backend python manage.py seed_demo_data
```

Full details — including the Cabinet question import — are in
[`LOCAL_DEVELOPMENT.md`](LOCAL_DEVELOPMENT.md).

## CI/CD pipeline

Every push runs [`.github/workflows/ci-cd.yaml`](.github/workflows/ci-cd.yaml).
The gates:

| Job | What it checks |
| --- | --- |
| **Workflow Lint** | `actionlint` on the workflows |
| **Lint** | `black` · `isort` · `flake8` (backend) |
| **Type Check** | `mypy` (backend) |
| **Security** | `pip-audit` (backend deps) |
| **Test** | `pytest` + migration drift check (`makemigrations --check`); SQLite in-memory, no external services |
| **Frontend** | ESLint · `tsc` · Vitest · production build (`frontend_modern`) |
| **Frontend E2E** | Playwright smoke + axe accessibility checks |
| **Lighthouse** | runtime performance budget |
| **CodeQL / Dependency Review** | code scanning + PR dependency diff |

When the gates pass on a deploy branch, **Build & Publish** builds the two
production images and pushes them to GHCR, then **Deploy** rolls them out to the
k3s cluster (image pinned by commit SHA, `kubectl rollout status` waited on).

### Branch → environment model

```
feature/*  ──PR──▶  modernization  ──PR──▶  qa  ──(CI builds + deploys)──▶  production (openshiksha.org)
   dev work          integration            release branch
```

- **`modernization`** — active development / integration branch; feature PRs land here.
- **`qa`** — the release branch. A merge here builds the images and **deploys to
  production** (`openshiksha.org`) automatically.
- A dedicated **qa environment** (taking `modernization`) is wired but disabled
  until a second cluster exists — see the `deploy-qa` job, gated behind the
  `QA_ENV_ENABLED` variable.

Deployment specifics (k3s, kustomize overlays, secrets, TLS, rollback) are in
[`docs/deploy/README.md`](docs/deploy/README.md).

## Documentation

- [Local development](LOCAL_DEVELOPMENT.md) — full setup, seeding, cabinet import
- [Deployment](docs/deploy/README.md) — k3s deploy, overlays, TLS, rollback
- [Git strategy](GIT_STRATEGY.md) — branch model and conventions
- [Initiatives](docs/initiatives/README.md) — long-horizon roadmap
- [Transactional emails](docs/emails.md) — branded email system

## Contributing

Contributions welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the
branch model, commit/PR conventions, and how to run the test suite locally.
Pre-commit hooks (`black`, `isort`, `flake8`, …) run on every commit — install
them with `pre-commit install`.

## License

OpenShiksha is licensed under the **Mozilla Public License 2.0** (MPL-2.0) — see
[`LICENSE.md`](LICENSE.md) for the full text.
