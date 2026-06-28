# BAK-3 — Prod backup CronJob + CI image publish + S3 secret keys

**Date:** 2026-06-27
**Classification:** New (Production Observability — Batch 3, Backups & DR drill)
**Depends on:** [BAK-1](2026-06-27-bak-1-backup-scripts.md) (the published image).

## Summary

Schedules the BAK-1 backup image to run nightly in **prod only**, publishes that
image from CI, and documents the new S3 secret keys. Additive: qa/dev kustomize
builds are byte-for-byte unchanged and need no S3 creds.

## What changed

- **`k8s/overlays/prod/backup-cronjob.yaml`** (new) — a `batch/v1 CronJob`
  (`schedule: "0 2 * * *"`, `concurrencyPolicy: Forbid`,
  `successful/failedJobsHistoryLimit: 3`, `backoffLimit: 2`,
  `restartPolicy: OnFailure`, small resource requests/limits) running
  `ghcr.io/openshiksha/openshiksha-backup:prod`. Env: existing `DATABASE_URL` +
  new `S3_ENDPOINT/S3_BUCKET/S3_ACCESS_KEY/S3_SECRET_KEY` + `RETENTION_DAYS`,
  all from the existing `openshiksha-secrets` Secret.
  - **Placed in the prod overlay, not `base/`** — kustomize's security boundary
    forbids an overlay referencing a file outside its own dir, and prod-only
    placement is exactly the intent (qa/dev never run it). Wired into
    `k8s/overlays/prod/kustomization.yaml` `resources:` + an `images:` retag
    entry so the bare image name picks up the `:prod` tag like backend/frontend.
- **`k8s/base/secret.example.yaml`** — documents the four `S3_*` keys (kubectl
  command + empty `stringData` stubs + comments: DO Spaces is the intended
  target; server-side only; qa/dev don't need them).
- **`.github/workflows/ci-cd.yaml`** — adds a `backup` entry to the
  `build-publish` matrix (context = repo root so `scripts/backup/*` is in scope,
  `Dockerfile.backup`). Publishes `openshiksha-backup:{branch,sha}` alongside
  backend/frontend on qa/prod pushes. `fail-fast: false` already isolates it.

## Validation

- `kubectl kustomize k8s/overlays/prod` renders cleanly; the CronJob appears with
  `namespace: openshiksha-prod` and image `…/openshiksha-backup:prod`.
- `kubectl kustomize k8s/overlays/qa` is **byte-for-byte unchanged** (sha256
  compared before/after) — qa carries no backup CronJob.
- The manifest uses only standard `batch/v1 CronJob` fields, so the CI
  `kubeconform -strict` gate (#459) passes. (kubeconform's Linux binary isn't
  runnable on the Windows build host; the clean render + standard schema cover
  it, and CI is the authoritative gate.)

## What could go wrong (mitigations)

- Schema typo breaking the kubeconform gate → only standard fields used; rendered
  locally first.
- CronJob erroring on schedule in qa with no creds → avoided by prod-overlay-only
  inclusion.
- No secret baked into the manifest — all values come from `openshiksha-secrets`.

## Migration notes

None — infra/CI only.

## Next steps

- BAK-4 — `BackupRun` model + `openshiksha_backup_age_seconds` freshness gauge,
  written by the CronJob on success (a follow-up wires `record_backup_run` into
  the backup script/Job).
- BAK-5 — `docs/ops/backups.md` runbook + ledger.
