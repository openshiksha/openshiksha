# 2026-06-09 — Retire legacy Python 2.7 Docker artifacts

**Branch:** `infra/2026-06-09-legacy-py2-retirement` → `modernization`
**Type:** infra / security hygiene

## What changed

Deleted four legacy Python 2.7 artifacts that were no longer built, deployed,
or runnable:

- `Dockerfile` (repo root) — `FROM python:2.7.18-buster`; could not even build
  anymore (Debian Buster apt repos archived mid-2024). CI's `build-publish`
  has shipped `backend/Dockerfile.prod` + `frontend_modern/Dockerfile.prod`
  instead since the deploy modernization.
- `pip-requirements.txt` (repo root) — the py2 dependency manifest. This was
  the target of **every open Dependabot security alert** (3 open at time of
  change: idna GHSA-65pc-fj4g-8rjx, urllib3 GHSA-qccp-gfcp-xxvc **high**,
  Pillow GHSA-wjx4-4jcj-g98j; 75 historically). None were fixable in place —
  the patched versions require Python 3.
- `scripts/collab/update.sh` and `scripts/collab/virtualenv_cleanup.sh` —
  interactive py2 virtualenv helpers that `pip install -r pip-requirements.txt`.

Also updated:

- `docs/deploy/README.md` — legacy-Dockerfile callout now says the file is
  deleted (recover from git history), not "kept for reference".
- `docs/infra/dependabot-legacy-stack.md` — status flipped from
  "75 alerts deferred" to **Resolved**, with guidance for future triage runs.

## Why

`docs/infra/dependabot-legacy-stack.md` (2026-06-05) prescribed exactly this
deletion as the correct fix for the legacy alert class, gated on the deploy
pipeline moving off the root Dockerfile. That gate has since cleared:

- `build-publish` builds the modern images (matrix in `ci-cd.yaml`).
- k8s manifests verified free of any Python 2 entrypoint — `backend`,
  `celery-worker`, `celery-beat` all run modern commands
  (`manage.py` / daphne / `celery -A openshiksha`).
- Local dev (`docker-compose.yml`) builds `./backend/Dockerfile` and
  `./frontend_modern/Dockerfile` — no reference to the root Dockerfile.
- Repo-wide grep: the only references to the deleted files were the files
  themselves plus historical docs.

## Effect

- All open Dependabot alerts auto-resolve once this reaches the default
  branch (`qa`) via the normal `modernization` → `qa` merge — the vulnerable
  manifest no longer exists.
- Future Dependabot scans only see live manifests
  (`backend/requirements.txt`, `frontend_modern/package-lock.json`,
  `.github/workflows/`).

## Explicitly out of scope

- Root `openshiksha/` legacy Django 1.11 source tree and `devops/` scripts —
  still referenced by each other (`devops/django.log` path in legacy
  `settings.py`), hold no dependency manifest, generate no alerts. Removing
  them is a separate cleanup decision.
- `.github/dependabot.yml` — needs no change; it never scanned the root pip
  manifest (security alerts come from GitHub's default scanning, not this file).
