# Dependabot triage — legacy Python 2.7 stack

**Date:** 2026-06-05 (resolved 2026-06-09)
**Status:** ✅ **Resolved** — the legacy manifest is gone. `pip-requirements.txt`,
the root `Dockerfile`, and the `scripts/collab/` venv helpers were deleted on
2026-06-09 (see [docs/changes/2026-06-09-legacy-py2-retirement.md](../changes/2026-06-09-legacy-py2-retirement.md)).
Dependabot alerts against `pip-requirements.txt` auto-resolve once the deletion
reaches the repo's default branch (`qa`) via the normal `modernization` → `qa` merge.

## Summary (as of resolution)

| Manifest | Owner stack | State |
|---|---|---|
| `pip-requirements.txt` (repo root) | **Legacy** Python 2.7 — was built by the root `Dockerfile` | **Deleted 2026-06-09.** Was already excluded from CI/deploy; Debian Buster base repos were archived mid-2024 so the image could not even build. |
| `backend/requirements.txt` | **Modern** Python 3.11 — built by `backend/Dockerfile.prod`, used by all CI (`lint`, `typecheck`, `security`, `test`) | Active. pip-audit runs on it in CI and is green. |

## History

On 2026-06-05 every open Dependabot alert (75 at the time) pointed at the
legacy py2 manifest. They were deferred rather than bumped because:

1. **No Python-2-compatible patched versions existed** for most advisories
   (Django 1.11 was the last py2 LTS; `pycrypto` was abandoned with no patch;
   Pillow/urllib3 fixes never backported to py2-compatible lines).
2. **No CI exercised the py2 stack**, so a blind bump would have shipped
   un-tested.
3. At the time of writing, the doc believed `build-publish` still shipped the
   root `Dockerfile`. That was retired separately — `build-publish` now builds
   `backend/Dockerfile.prod` and `frontend_modern/Dockerfile.prod` (see
   [docs/deploy/README.md](../deploy/README.md)).

The prescribed fix was to delete the legacy artifacts rather than maintain a
py2 requirements file. With the deploy pipeline already fully on the modern
images and the k8s manifests verified free of any Python 2 entrypoint, that
deletion landed 2026-06-09.

Note: the legacy Django 1.11 source tree (root `openshiksha/` package) and the
`devops/` nginx/gunicorn scripts it references are still in the repo. They hold
no dependency manifest, so they generate no Dependabot alerts; removing them is
cleanup, not security work.

## What the dependabot routine should do now

- Triage alerts on `backend/requirements.txt`, `frontend_modern/package.json`,
  and `.github/workflows/*.yaml` — these are the only live manifests.
- If an alert still shows against `pip-requirements.txt`, check whether the
  deletion has reached the default branch (`qa`) yet; do not re-add the file.
