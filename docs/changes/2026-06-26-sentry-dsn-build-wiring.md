# Wire Sentry DSNs into the build/deploy (OBS-3 / OBS-5 activation)

## Summary
Completes the OBS-3/OBS-5 follow-up: makes the env-gated Sentry wiring actually
reachable in deployed builds. The **frontend** DSN is injected into the prod image
at build time from a GitHub Actions secret; the **backend** DSN key is documented
in the cluster Secret template (set out-of-band on the cluster).

## Classification
Improve / ops wiring (no app code change).

## What changed
- **`frontend_modern/Dockerfile.prod`** — added `ARG VITE_SENTRY_DSN=` + `ENV`
  before `npm run build` so Vite inlines it. Empty default ⇒ reporting disabled
  and Rollup drops the SDK (entry chunk unchanged), so local/uncfg builds are
  byte-for-byte today's.
- **`.github/workflows/ci-cd.yaml`** — the image build-push step passes
  `VITE_SENTRY_DSN=${{ secrets.VITE_SENTRY_DSN }}` as a build-arg (alongside the
  existing GIT_SHA/BUILD_TIME). The backend image ignores the undeclared ARG
  harmlessly. The secret is masked in CI logs.
- **`k8s/base/secret.example.yaml`** — documented the optional backend
  `SENTRY_DSN` key (server-side only; recommend a *separate* Sentry project from
  the frontend so Python/Django events don't mix with browser events).

## Secret handling
- **Frontend DSN** → GitHub Actions secret `VITE_SENTRY_DSN`. Not in the source
  tree, masked in CI logs, not readable by collaborators in settings. Note: a
  frontend DSN is inlined into the public JS bundle by design (true for any
  browser SDK) — it is not a confidential value; Sentry-side rate limits / allowed
  domains are the real protection.
- **Backend DSN** → the cluster Secret `openshiksha-secrets` (created out-of-band,
  never committed). Set with, e.g.:
  ```
  kubectl -n openshiksha-prod patch secret openshiksha-secrets --type merge \
    -p '{"stringData":{"SENTRY_DSN":"https://...@oNNN.ingest.sentry.io/NNN"}}'
  kubectl -n openshiksha-prod rollout restart deploy/backend deploy/celery-worker
  ```

## How to verify
- Frontend: after a CI build with the secret set, the shipped bundle initialises
  Sentry; with the secret empty, no Sentry code ships (`check:budget` still green).
- Backend: with `SENTRY_DSN` present in the pod env, `init_sentry()` returns True;
  empty/unset ⇒ no-op.

## Notes / follow-ups
- The given DSN is a **frontend (React) project** DSN. Backend error tracking
  should use a **separate Sentry project**; reusing the frontend DSN mixes
  platforms in one project (works, but not recommended).
- Backend DSN must be set on the cluster Secret (manual step above) — it is not
  driven by CI, since `openshiksha-secrets` is bootstrapped out-of-band.
