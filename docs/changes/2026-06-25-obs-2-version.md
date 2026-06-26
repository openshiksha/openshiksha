# OBS-2 — `/api/v1/version/` build-info endpoint

## Summary
Adds a trivial, DB-free, public `/api/v1/version/` endpoint that reports which
build is live (version, git sha, build time, environment) so an operator can
correlate a prod incident with a specific image. The git sha + build time are
baked into the prod image at build time via Docker `ARG`s passed from CI.

## Classification
New.

## Legacy files referenced
None — observability is greenfield.

## What changed
- **`backend/openshiksha/settings/base.py`** — added `APP_VERSION`
  (`env APP_VERSION`, default `"2.0.0"`) and `ENVIRONMENT`
  (`env ENVIRONMENT`, default `"development"`).
- **`backend/openshiksha/apps/api/views/version.py`** (new) — `version_info`,
  an `AllowAny` DRF view returning `{version, git_sha, built_at, environment}`.
  `git_sha`/`built_at` come from env (`GIT_SHA`/`BUILD_TIME`), defaulting to
  `"unknown"`. **No secrets, ever.**
- **`backend/openshiksha/apps/api/urls.py`** — mounted
  `path("version/", version_info, name="version_info")`.
- **`backend/Dockerfile.prod`** — `ARG GIT_SHA`/`ARG BUILD_TIME` → `ENV` (default
  `unknown` for local builds).
- **`.github/workflows/ci-cd.yaml`** — the image build-push step now passes
  `--build-arg GIT_SHA=${{ github.sha }}` and a `date -u` build time (new
  `build_time` output on the extract-branch step). The frontend image ignores the
  extra ARGs harmlessly.

## Tests written
`backend/openshiksha/apps/api/tests/test_version_api.py` (5 tests, all green):
- returns exactly the four keys; reflects `APP_VERSION`/`ENVIRONMENT` settings;
  `git_sha`/`built_at` default to `"unknown"` when env unset; reads `GIT_SHA`/
  `BUILD_TIME` env when set; accessible unauthenticated.

## Migration notes
None — no model changes.

## How to verify
- `pytest openshiksha/apps/api/tests/test_version_api.py` (5 pass).
- `curl :8000/api/v1/version/` → JSON with the four keys; `git_sha`/`built_at`
  show the baked image values in a CI-built image, `"unknown"` locally.

## Next steps
OBS-3 (backend Sentry, env-gated) → OBS-4 (request-id + JSON logs) → OBS-5
(frontend error reporting).
