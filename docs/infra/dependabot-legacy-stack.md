# Dependabot triage — legacy Python 2.7 stack

**Date:** 2026-06-05
**Status:** All open Dependabot alerts (75 at time of writing) are deferred — see "Why" below.

## Summary

| Manifest | Open alerts | Owner stack | Action |
|---|---|---|---|
| `pip-requirements.txt` (repo root) | 75 | **Legacy** Python 2.7 — built by root `Dockerfile`, deployed to GHCR by `build-publish` on `qa`/`prod` | Deferred — see below |
| `backend/requirements.txt` | 0 | **Modern** Python 3.11 — built by `backend/Dockerfile`, used by all CI (`lint`, `typecheck`, `security`, `test`) | Already patched (Django 4.2.30, Pillow 12.2.0, requests 2.33.0, urllib3 transitive via requests, etc.) |

Every alert points at `pip-requirements.txt`. The modernized backend manifest
(`backend/requirements.txt`) is clean of open advisories — pip-audit already
runs on it in CI and is green.

## Why none of the 75 alerts were auto-fixed

1. **The vulnerable file is the deployed artifact, not dead code.**
   `.github/workflows/ci-cd.yaml` (`build-publish` job) runs
   `docker/build-push-action` with `context: .` and no `file:` override, so it
   builds the **root `Dockerfile`** — which is `FROM python:2.7.18-buster` and
   `pip install -r pip-requirements.txt`. That image is the one `kubectl rollout
   restart` ships to prod. A blind bump of these pins can break the deployed
   container.

2. **Many alerts have no Python-2-compatible patched version.**
   - `Django==1.11.29` → Django 1.11 is the last py2 LTS; all patched
     Django alerts (4.2.x range) require Python 3.
   - `pycrypto==2.6.1` (alerts #1, #2) → no patch ever shipped; project is
     abandoned. Modern replacement is `pycryptodome`, but that is a code
     change, not a version bump.
   - `ecdsa` alert #90 → no patched version available.
   - `Pillow==3.3.2`, `urllib3==1.24.3`, etc. → patched versions exist, but the
     advisories Dependabot is matching against demand 2.x-only fixes that
     never backported to the 1.26 line.

3. **No safe CI to validate a py2 bump.** The Python 2.7 stack is not
   exercised by any CI job (`test` runs on the modern backend). Bumping pins
   here would land in prod un-tested.

## Recommended resolution

The correct fix is **not** to maintain a py2 requirements file — it is to
retire the root `Dockerfile` and ship the modern `backend/Dockerfile` from
`build-publish`. Concretely:

1. Switch `build-publish` to `file: backend/Dockerfile` (plus a matching
   frontend build for the SPA, or a multi-stage image).
2. Delete root `Dockerfile`, `pip-requirements.txt`,
   `scripts/collab/update.sh`, `scripts/collab/virtualenv_cleanup.sh`.
3. Update `.github/dependabot.yml` to drop the root-level pip scan once
   `pip-requirements.txt` is gone (currently it only scans `/backend`, so no
   change needed there — see [.github/dependabot.yml](../../.github/dependabot.yml)).
4. Verify the K8s manifest (cluster `k3s-personal-server`) does not depend on
   any Python 2 entrypoint (`devops/run-production-server.sh`).

This is initiative-sized work, not a single PR. Suggested promotion path:
write it up as `docs/initiatives/legacy-docker-retirement.md` and add a row
to `docs/initiatives/STATUS.md`.

Until then, the 75 alerts on `pip-requirements.txt` are **intentionally
deferred** and should not be re-triaged file-by-file.

## What the dependabot routine should do in the meantime

- Skip the legacy `pip-requirements.txt` alerts (link this doc when reporting).
- Continue to triage any new alerts on `backend/requirements.txt`,
  `frontend_modern/package.json`, and `.github/workflows/*.yaml`.
- Re-evaluate this doc once the legacy Docker retirement initiative is
  promoted or done.
