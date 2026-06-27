# MET-5 — Grafana starter dashboard + scrape runbook + Batch 2 close-out

**Date:** 2026-06-27
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md) — Batch 2, increment 5 of 5 (close-out)
**Plan:** [2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)
**Classification:** New / Docs

## Summary

Closes Observability Batch 2 (Metrics & dashboards). Docs/config only — no code
paths touched. Gives an operator a one-import Grafana board over the MET-1..4
signals and a runbook for enabling + scraping `/metrics` safely.

## What changed

- `docs/ops/grafana/openshiksha-overview.json` — importable Grafana dashboard
  (templated `DS_PROMETHEUS` datasource, no org-specific UID): request rate +
  p95 latency (MET-4), grade-queue depth + active assignments (MET-2), Celery
  failures + oldest-pending age (MET-3), process RSS + build-info (MET-1).
- `docs/ops/metrics.md` — runbook: enable steps (`METRICS_ENABLED` /
  `METRICS_TOKEN`), in-cluster scrape config (static + ServiceMonitor), the
  **not-publicly-routed** exposure note, the single-daphne-process assumption,
  the MET-3 `CELERY_RESULT_BACKEND=django-db` dependency, and the full metric
  catalogue.
- `docs/initiatives/2026-production-observability.md` — Batch 2 table flipped to
  ✅ with PR links; "Later batches" marks Batch 2 shipped; ledger row appended.
- `docs/initiatives/STATUS.md` — Production-Observability row updated: Batch 2
  shipped, **Next increment → Batch 3 (Backups & DR drill)**.

## Verify

- `python -m json.tool docs/ops/grafana/openshiksha-overview.json` parses.
- Markdown links resolve.

## Migration notes

None.

## Next steps

Batch 3 — Backups & DR drill (automated Postgres dump → object storage + a
documented, *tested* restore runbook).
