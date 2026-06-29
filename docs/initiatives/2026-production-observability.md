# Production Observability & Operational Readiness

**Status:** ✅ **North Star reached** (Batch 4 shipped 2026-06-28) · **Owner:** `openshiksha-plan` / `openshiksha-execute` routines

> The operability spine is complete: **observable** (Batch 1) → **measurable**
> (Batch 2) → **recoverable** (Batch 3) → **alerting** (Batch 4). No unblocked next
> bet remains here — the next planning run **promotes a fresh top initiative** (see
> the close-out note at the end of the Batch-4 backlog).

> Not owned by the `openshiksha-ai-features` routine. This is general
> foundation-hardening and is the top active initiative on
> [`STATUS.md`](STATUS.md).

---

## North Star

OpenShiksha is **live in production** (DigitalOcean droplet, k3s, `openshiksha.org`)
but is effectively **flying blind**: when something breaks in prod there is no
error tracking, the readiness probe never checks the DB/cache, logs are
unstructured plain text with no request correlation, and a frontend crash is
invisible to operators. The North Star: **a clean-checkout operator can see,
within minutes, that something is wrong, what it is, and which request caused
it** — without SSHing into a pod to grep a rotating file.

Every increment is **additive and env-gated**: nothing changes local-dev or CI
behaviour unless an ops env var (`SENTRY_DSN`, `VITE_SENTRY_DSN`,
`LOG_FORMAT=json`) is set. No new always-on runtime dependency that the perf
budget or the offline story would notice.

## Why this exists

The platform is feature-complete (AI, a11y, mobile/PWA, i18n all shipped and
gated) and **in production**, but operability has not kept pace with features.
The biggest pre-launch risk is no longer "missing a feature" — it's "a prod
incident nobody can diagnose." This initiative closes that gap with small,
low-risk, independently-shippable PRs, in the plan/execute routines' lane
(infra + backend + a thin frontend slice).

## Grounded current state (verified 2026-06-25)

- **Liveness:** `GET /healthz/` ([backend/openshiksha/urls.py](../../backend/openshiksha/urls.py))
  — deliberately cheap (no DB/Redis). Its **own docstring** says: *"DB-aware
  probes belong on a separate `/readyz` that the LB can use as a drain signal."*
  That `/readyz` was never built.
- **Deep check exists but is mis-wired:** `GET /api/v1/health/`
  ([apps/api/views/health.py](../../backend/openshiksha/apps/api/views/health.py))
  *does* verify DB + cache and returns 503 on failure — but **nothing probes
  it.** The k8s **readinessProbe** ([k8s/base/backend.yaml](../../k8s/base/backend.yaml):61)
  points at the cheap `/healthz/`, so a pod with a dead DB connection is still
  sent traffic.
- **No error tracking:** `sentry` appears nowhere in `backend/requirements.txt`
  or the frontend deps. Prod exceptions die in a rotating log file.
- **Unstructured logs:** [settings/base.py](../../backend/openshiksha/settings/base.py):292
  `LOGGING` has only `verbose`/`simple` text formatters and **no request
  correlation id** — you cannot tie a log line to the request that produced it.
- **Frontend blind:** a shared `ErrorBoundary`
  ([shared/ui/ErrorBoundary.tsx](../../frontend_modern/src/shared/ui/ErrorBoundary.tsx))
  exists and renders a fallback, but it reports the caught error **nowhere**.

## Principles — the operability bar (every increment ships meeting all of these)

1. **Additive & env-gated.** No DSN / no `LOG_FORMAT=json` ⇒ behaviour is byte-for-byte
   today's. Proven by a test (init is a no-op when the env var is unset).
2. **Never break the probe contract.** Liveness stays cheap and DB-independent; a
   DB blip must not kill the pod, only drain it from the LB via readiness.
3. **No secrets in logs/errors.** Scrub auth headers, tokens, passwords, and
   `ANTHROPIC_API_KEY` before anything leaves the process.
4. **No perf/offline regression.** The frontend slice stays outside the
   ~160 kB entry-budget guard (lazy/gated import); the SW + persister are untouched.
5. **Tested in the same increment** — backend `pytest`, frontend Vitest — covering
   the gated-on path **and** the gated-off (default) path.

## Backlog — Batch 1 (PR-sized, lowest-risk-first)

| ID | Increment | Classify | Status |
|----|-----------|----------|--------|
| OBS-1 | **`/readyz/` deep readiness endpoint + repoint the k8s readinessProbe.** Add a top-level `readyz` view (DB + cache check, 503 on failure — reuse the `/api/v1/health/` logic, kept Host-header-cheap), keep `/healthz/` as liveness. Repoint `k8s/base/backend.yaml` readinessProbe `path: /healthz/ → /readyz/`; liveness unchanged. Builds the design the `healthz` docstring already specified. Tests: `readyz` 200 when up, 503 when DB/cache down (mock the failure); `healthz` stays DB-free. | Improve | ⬜ |
| OBS-2 | **`/api/v1/version/` build-info endpoint.** Returns `{version, git_sha, built_at, environment}` from env (`GIT_SHA`, `BUILD_TIME` baked at image build, `DJANGO_ENV`). `AllowAny`, no secrets. Lets an operator confirm *which* build is live. Wire `GIT_SHA`/`BUILD_TIME` ARGs into `Dockerfile.prod` + the CI publish step. Tests: shape + defaults when env unset. | New | ⬜ |
| OBS-3 | **Sentry error tracking (backend), env-gated.** Add `sentry-sdk[django]` to requirements; `sentry_sdk.init` in `settings/production.py` **only when `SENTRY_DSN` is set**, with Django + Celery + Redis integrations, `traces_sample_rate` from env (default 0), `send_default_pii=False`, and a `before_send` scrubber dropping auth headers + known secret keys. Tests: init is a **no-op** without DSN; the scrubber strips an `Authorization` header / `password` field. | New | ⬜ |
| OBS-4 | **Request-correlation id + JSON log option.** A lightweight middleware that reads/generates `X-Request-ID`, stashes it in a contextvar, echoes it on the response, and a logging filter that injects it into every record; add an opt-in `json` formatter (`LOG_FORMAT=json` ⇒ JSON handler, else today's text). When OBS-3 is present, tag the Sentry scope with the request id. Tests: middleware round-trips a supplied id + generates one when absent; JSON formatter emits parseable JSON incl. `request_id`. **Soft-depends on OBS-3** (Sentry scope tagging is a no-op if Sentry absent). | Improve | ⬜ |
| OBS-5 | **Frontend error reporting, env-gated.** Wire `@sentry/react` into the existing `ErrorBoundary` + app root **only when `VITE_SENTRY_DSN` is set** (dynamic import so the entry chunk is unchanged when unset — perf budget defended); the boundary's `componentDidCatch` forwards to Sentry; friendly localized fallback (LA i18n) stays. Tests (Vitest): boundary renders the fallback on a child throw with **no** DSN (no import, no crash); reporter helper is a no-op when DSN unset. | New | ⬜ |

**Batch 1 build order:** OBS-1 → OBS-2 → OBS-3 → OBS-4 → OBS-5. Items are
largely **independent**; the only soft edge is OBS-4→OBS-3 (request-id Sentry
tagging). Ship lowest-risk-first; one failure does not block the rest.

**Batch 1 DoD:** a prod incident is now *observable* — readiness drains a pod
with a broken DB, every backend exception lands in Sentry (when DSN set) tagged
with a correlatable request id, an operator can read `/api/v1/version/` to know
the live build, logs can be shipped as JSON, and a frontend crash reports
instead of vanishing — all **without** changing local-dev or CI defaults.

## Backlog — Batch 2 (Metrics & dashboards · PR-sized, lowest-risk-first)

Scoped 2026-06-27 ([2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)).
Verified greenfield: `prometheus`/`/metrics` appear nowhere in `backend/`;
`django-celery-results` **is** installed (MET-3 reads `TaskResult`, no new dep);
prod runs a **single daphne** ASGI process (default registry is correct — no
`PROMETHEUS_MULTIPROC_DIR`); Celery is a **separate worker** (so MET-2/3 compute
on-scrape from the DB, not from in-worker counters); the ingress routes only
`/api`,`/django-admin`,`/static`,`/` so a top-level `/metrics` is **not publicly
routable** (internal-only via `backend:8000`).

| ID | Increment | Classify | Status |
|----|-----------|----------|--------|
| MET-1 | **`prometheus-client` dep + gated `/metrics` exposition endpoint.** Top-level `/metrics` view (`apps/core/metrics.py`, mounted from `urls.py` like `readyz`) exposing the default registry (process + GC); gated behind `METRICS_ENABLED` (default off ⇒ **404**, byte-for-byte today's) + optional `METRICS_TOKEN` bearer (mismatch ⇒ 403). Use `prometheus-client`, **not** always-on `django-prometheus`. Tests: 404 disabled / 200 enabled / 403 bad token. | New | ✅ [#467](https://github.com/openshiksha/openshiksha/pull/467) |
| MET-2 | **Business & queue-depth gauges (on-scrape collector).** A custom `Collector` running read-only ORM COUNTs at scrape time — `openshiksha_assignments_active`, `_submissions_pending_grading` (**grade-queue depth**), `users{role}`, classroom/subjectroom counts. Registered lazily on first enabled scrape. Tests: gauges reflect seeded data; absent + no DB hit when disabled. | New | ✅ [#468](https://github.com/openshiksha/openshiksha/pull/468) |
| MET-3 | **Async-task health gauges from `TaskResult` (on-scrape).** Celery health derived from `django_celery_results.TaskResult` (24h window): `openshiksha_celery_tasks{status}` + `_celery_oldest_pending_seconds` — avoids cross-process counter aggregation. Gated on the result-backend being `django-db` (honest no-op under the default Redis backend). Tests: seeded SUCCESS/FAILURE rows reflected; absent under Redis backend. | New | ✅ [#470](https://github.com/openshiksha/openshiksha/pull/470) |
| MET-4 | **HTTP request metrics middleware (gated).** `MetricsMiddleware` (after `RequestIDMiddleware`) recording `openshiksha_http_requests_total{method,status_class}` + `_http_request_duration_seconds` histogram; pure pass-through when disabled; label by method/status-class (no raw-path cardinality). Tests: counters move when enabled; no movement when disabled. | New | ✅ [#471](https://github.com/openshiksha/openshiksha/pull/471) |
| MET-5 | **Grafana starter dashboard + scrape runbook + ledger.** `docs/ops/grafana/openshiksha-overview.json` (request rate/p95, grade-queue depth, Celery failures/oldest-pending, process RSS, build info) + `docs/ops/metrics.md` (enable steps, in-cluster scrape config, not-publicly-routed note, single-process + `TaskResult` dependencies, metric catalogue) + `STATUS.md`/ledger update. Docs-only — safe last. | New / Docs | ✅ (this PR) |

**Batch 2 build order:** MET-1 → (MET-2, MET-3, MET-4 independent) → MET-5.
MET-2/3/4 depend only on MET-1's registry + endpoint; MET-5 is pure docs.

**Batch 2 DoD:** an operator can scrape a gated `/metrics`, point Prometheus at
it in-cluster, and watch the signals that predict an OpenShiksha incident
(grade-queue depth, Celery failure rate, request latency) on an importable
Grafana board — all **off by default** (404 + no DB work when `METRICS_ENABLED`
is unset), no new always-on agent, no perf/offline regression.

## Backlog — Batch 3 (Backups & DR drill · PR-sized, lowest-risk-first)

Scoped 2026-06-27 ([2026-06-27-plan-2.md](../daily-plans/2026-06-27-plan-2.md)).
Verified greenfield: `k8s/base/postgres.yaml` is a single `postgres:15-alpine`
StatefulSet (`replicas: 1`, one 10 Gi PVC) with **no backup mechanism** —
no `CronJob`, no `pg_dump`, no object-storage wiring anywhere in `k8s/` or
`scripts/`. `DATABASE_URL` lives in `openshiksha-secrets`; the
`kustomize build | kubeconform -strict` manifest gate (#459) runs in `ci-cd.yaml`.
Prod overlay namespace is `openshiksha-prod`.

| ID | Increment | Classify | Status |
|----|-----------|----------|--------|
| BAK-1 | **Backup/restore scripts + version-matched dump image.** `scripts/backup/pg_backup.sh` (custom-format `pg_dump` → gzip → S3-compatible upload via static `mc` → prune by `RETENTION_DAYS`) + `pg_restore.sh` (guarded by `CONFIRM=1`) + `backend/Dockerfile.backup` (`FROM postgres:15-alpine` so `pg_dump` major matches the server). Touches nothing live. | New | ✅ [#474](https://github.com/openshiksha/openshiksha/pull/474) |
| BAK-2 | **Local, tested backup→restore round-trip drill.** `scripts/backup/drill.sh` runs entirely against the docker-compose Postgres: seed → dump (local mode, no cloud creds) → drop/recreate scratch DB → restore → **assert row-count parity**. The "*tested* restore runbook" half of the DoD. Depends on BAK-1. | New | ✅ [#475](https://github.com/openshiksha/openshiksha/pull/475) |
| BAK-3 | **Prod backup `CronJob` (prod-overlay-only, additive).** `k8s/overlays/prod/backup-cronjob.yaml` (nightly, `concurrencyPolicy: Forbid`) running the BAK-1 image, referenced only from the prod overlay so qa/dev kustomize builds are byte-for-byte unchanged; new `S3_*` keys documented (empty) in `secret.example.yaml`; passes the `kubeconform -strict` gate. Image published via CI (`build-publish` matrix). Depends on BAK-1. | New | ✅ [#476](https://github.com/openshiksha/openshiksha/pull/476) |
| BAK-4 | **Backup-freshness gauge (reuses the MET-2 collector).** A `BackupRun` model + migration + `record_backup_run` management command the CronJob calls on success, surfaced as `openshiksha_backup_age_seconds` / `_last_success_timestamp` on the existing `BusinessMetricsCollector` — same gated, on-scrape, read-only pattern; honest empty-history case. Gives Batch 4 a concrete signal to alert on. | New | ✅ [#477](https://github.com/openshiksha/openshiksha/pull/477) |
| BAK-5 | **`docs/ops/backups.md` runbook + ledger.** Architecture, schedule, retention/RPO/RTO, the restore drill (local via BAK-2 + prod via a one-off restore Job), the new secret keys, the freshness metric + suggested alert threshold; `STATUS.md` + ledger update (Batch 3 → shipped, Next → Batch 4). Docs-only — safe last. | New / Docs | ✅ (this PR) |

**Batch 3 build order:** BAK-1 → (BAK-2, BAK-3, BAK-4 independent) → BAK-5.
All four feature PRs hang off BAK-1; BAK-5 is docs.

**Batch 3 DoD:** the live Postgres has off-site, retained, version-matched
nightly dumps; the restore path is **actually exercised** (BAK-2 round-trip,
asserted), not merely documented; a backup-freshness gauge feeds Batch 4 — all
additive (qa/dev untouched, no secret committed, the manifest gate green).

## Backlog — Batch 4 (Uptime & alerting · PR-sized, lowest-risk-first) ✅ SHIPPED 2026-06-28

Scoped 2026-06-28 ([2026-06-28-plan.md](../daily-plans/2026-06-28-plan.md)).
Verified greenfield: no `alertmanager`, `PrometheusRule`, alert-rule file, or
uptime check existed anywhere in `k8s/`, `scripts/`, or `docs/ops/`; **no
Prometheus is deployed in `k8s/`** (the Batch-2 `/metrics` + Grafana JSON are
operator drop-in artifacts). Batch 4's rule/Alertmanager files follow the same
"artifact, not deployment" model, and ALT-3 deliberately needs **no** monitoring
stack. Every alert fires on a metric `apps/core/metrics.py` already emits.

| ID | Increment | Classify | Status |
|----|-----------|----------|--------|
| ALT-1 | **Prometheus alerting-rules artifact.** `docs/ops/prometheus/openshiksha-alerts.yml` — 8 alerts against the existing metrics (backup stale/never-run, grade-queue backlog, Celery failure-rate/oldest-pending, HTTP 5xx ratio, p95 latency, target-down), every metric cross-checked against `apps/core/metrics.py`; `promtool`-clean. Pure artifact — touches nothing live. | New / Docs | ✅ [#481](https://github.com/openshiksha/openshiksha/pull/481) |
| ALT-2 | **Alertmanager config + ntfy bridge.** `docs/ops/alertmanager/alertmanager.yml` (route → single webhook receiver; commented email alternative) + `scripts/ops/alert_to_ntfy.py` (stdlib bridge, **no new pip dep**, pure `format_alert`/`format_payload`, ntfy URL from env never logged) + 7 formatter unit tests; `amtool`-clean. | New | ✅ [#482](https://github.com/openshiksha/openshiksha/pull/482) |
| ALT-3 | **Standalone in-cluster uptime probe CronJob (prod-overlay-only).** `scripts/ops/uptime_probe.sh` (curls `/healthz/`+`/readyz/`, pushes one DOWN alert to ntfy on any non-200, exits non-zero; success silent) baked into the BAK-1 backup image via a `command:` override + `k8s/overlays/prod/uptime-probe-cronjob.yaml` (every 5 min, `Forbid`); `ALERT_NTFY_URL`/`PROBE_BASE_URL` documented; kubeconform gate green, qa byte-for-byte unchanged. Works with **zero Prometheus**. | New | ✅ [#483](https://github.com/openshiksha/openshiksha/pull/483) |
| ALT-4 | **CI validation of the alerting artifacts.** Additive `alerting-lint` job running `promtool check rules` + `promtool test rules` (fixture: BackupStale fires at 37h not 1h) + `amtool check-config` + the ALT-2 bridge pytest. Pinned Prometheus 2.53.1 / Alertmanager 0.27.0. Makes the config "tested," not just committed. | Improve / Infra | ✅ [#484](https://github.com/openshiksha/openshiksha/pull/484) |
| ALT-5 | **`docs/ops/alerting.md` runbook + Sentry routing + close-out.** Alert catalogue (metric/expr/threshold/severity/**first response**), the Alertmanager→ntfy routing path, the uptime probe's role, how to wire Sentry's own issue-alert rules; `STATUS.md` + ledger update (Batch 4 → shipped, **North Star reached**). Docs-only — safe last. | New / Docs | ✅ (this PR) |

**Batch 4 build order:** ALT-1 → ALT-2 → ALT-3 → ALT-4 → ALT-5. ALT-1/2/3 are
mutually independent (lowest-risk-first); ALT-4 lints ALT-1/2's artifacts (stacked
on them); ALT-5 is docs.

**Batch 4 DoD:** an operator is *pushed* a notification when something is wrong.
Two layers: the **standalone ALT-3 probe alerts with zero monitoring stack** (the
active alarm today), and the **rule-based ALT-1/2/4 path** is committed +
CI-linted, ready to go live the moment Prometheus + Alertmanager are deployed.

**Close-out (2026-06-28):** the operability spine is complete (observable →
measurable → recoverable → **alerting**). **No unblocked next bet remains on this
board** — the next planning run promotes a fresh top initiative. Candidates: the
**AI-tutor rebase** (`ai/2026-06-04-ai-tutor-chat`; confirm it is *not* inside the
`ai-features` fence before promoting in this lane), an **`/ai/predictions/`
teacher surface** (a product call), or **un-pausing Interactive Widgets** (needs
product discovery). **Honest operational follow-up** (not blocking close):
Prometheus + Alertmanager are **not deployed** in `k8s/` yet — ALT-1/2/4 are
validated drop-in artifacts an operator activates; the standalone ALT-3 probe is
the only piece that alerts with zero stack.

## Later batches
- **Batch 2 — Metrics & dashboards. ✅ SHIPPED 2026-06-27** (MET-1..5,
  [#467](https://github.com/openshiksha/openshiksha/pull/467)–[#471](https://github.com/openshiksha/openshiksha/pull/471)):
  gated Prometheus `/metrics`, on-scrape business/queue-depth + `TaskResult`-derived
  Celery gauges, gated HTTP request metrics, Grafana starter + scrape runbook.
- **Batch 3 — Backups & DR drill. ✅ SHIPPED 2026-06-27** (BAK-1..5,
  [#474](https://github.com/openshiksha/openshiksha/pull/474)–[#477](https://github.com/openshiksha/openshiksha/pull/477) + this docs PR):
  version-matched dump tooling + a *tested* local restore drill (row-count parity)
  + a prod-only nightly `CronJob` + a backup-freshness gauge feeding Batch 4 — the
  data-loss insurance the live DB previously lacked.
- **Batch 4 — Uptime & alerting. ✅ SHIPPED 2026-06-28** (ALT-1..5,
  [#481](https://github.com/openshiksha/openshiksha/pull/481)–[#484](https://github.com/openshiksha/openshiksha/pull/484) + this docs PR):
  Prometheus alert-rules artifact (8 alerts on the existing metrics) → Alertmanager
  config + stdlib ntfy bridge → standalone in-cluster uptime probe CronJob (alerts
  with zero Prometheus) → `alerting-lint` CI gate (promtool/amtool + bridge tests) →
  `docs/ops/alerting.md` runbook + Sentry routing. **North Star reached.**

## Out of scope
- **APM vendor lock-in / always-on heavy agents.** Everything stays env-gated and
  removable; no agent runs by default in dev or CI.
- **Log-everything.** Structured logging is opt-in and scrubbed; we do not start
  logging request bodies or PII.

## Definition of Done (per increment)
- Meets the 5-point operability bar (additive · probe-safe · no secrets · no
  perf/offline regression · tested both gated-on and gated-off).
- Build/lint/types/tests green (`pytest` if backend; `npm run lint && npx tsc
  --noEmit && npx vitest run` if frontend).
- Ledger row appended below; this doc + `STATUS.md` updated when a batch lands.

## Progress Ledger

| Date | Increment | PR | Learning |
|------|-----------|----|----------|
| 2026-06-25 | Initiative promoted; Batch 1 (OBS-1..5) scoped. The board had **no unblocked next bet** (Accessibility closed today; OSS/Mobile/Language-Access Done; IW Paused; LA-10 blocked) and the platform is live in prod but un-observable. Grounded: `/healthz/` is cheap-by-design and its own docstring asks for the missing `/readyz`; `/api/v1/health/` does the deep check but nothing probes it; no Sentry; logs unstructured + uncorrelated; the shared `ErrorBoundary` reports nowhere. | _(this doc)_ | The readiness gap is not a redesign — the intended split (cheap liveness `/healthz/` + deep drain-signal `/readyz/`) is already written in the `healthz` docstring; OBS-1 just builds the half that was specified but never shipped. |
| 2026-06-27 | **Batch 2 (Metrics & dashboards) SHIPPED — MET-1..5.** Gated Prometheus `/metrics` (`METRICS_ENABLED`/`METRICS_TOKEN`, 404 by default; `prometheus-client`, not always-on `django-prometheus`) → on-scrape business/queue-depth gauges (lazy-registered, fault-tolerant `collect()`) → `TaskResult`-derived Celery health gated on the `django-db` result backend → gated HTTP request count + latency middleware → Grafana starter (`docs/ops/grafana/openshiksha-overview.json`) + scrape runbook (`docs/ops/metrics.md`). | [#467](https://github.com/openshiksha/openshiksha/pull/467)–[#471](https://github.com/openshiksha/openshiksha/pull/471) | On-scrape gauges (lazy DB COUNTs) beat in-process event counters for a separate-worker topology: stateless, no cross-process aggregation, and trivially zero-cost when disabled (endpoint 404s before any collector runs). The default Redis result backend means MET-3 ships as an *honest no-op* (gated on `django-db`) rather than a misleading constant zero. Stacked-PR lesson: after a squash-merge the stacked branch carries a duplicate of the merged commit — `git rebase --onto <new-base> <old-base> <branch>` drops it cleanly. |
| 2026-06-28 | **Batch 4 (Uptime & alerting) SHIPPED — ALT-1..5. North Star reached.** Prometheus alert-rules artifact (8 alerts, every metric cross-checked against `apps/core/metrics.py`; `clamp_min` denominators avoid divide-by-zero) → Alertmanager config + a dependency-light stdlib ntfy bridge (`scripts/ops/alert_to_ntfy.py`, pure formatter, ntfy URL from env never logged, resolved→never-pages) → a standalone prod-overlay-only uptime probe CronJob reusing the BAK-1 backup image via a `command:` override (alerts with **zero** Prometheus; qa byte-for-byte unchanged) → an `alerting-lint` CI gate (`promtool check/test rules` + `amtool check-config` + the bridge pytest, pinned binaries) → `docs/ops/alerting.md` runbook + Sentry issue-alert routing. | [#481](https://github.com/openshiksha/openshiksha/pull/481)–[#484](https://github.com/openshiksha/openshiksha/pull/484) + this PR | The operability spine closes as a **loop**: Batch 4 alerts on the *exact signals* the earlier batches emit (the BAK-4 freshness gauge → `OpenShikshaBackupStale`; the MET-2/3/4 gauges → queue/Celery/HTTP alerts). Two lessons. (1) **Config-as-code that references live metric names rots silently** — gate it like manifests: `promtool`/`amtool` in CI is the alerting analogue of the kubeconform gate; `promtool test rules` pins threshold semantics (fires at 37h, not 1h). (2) **A floor alarm beats a perfect one that isn't deployed** — no Prometheus runs in prod yet, so the dependency-free ALT-3 probe (curl + ntfy, no stack) is what actually pages today; the rule-based path is validated drop-in, dormant until the stack lands. Honest close: "done" ≠ "fully deployed" — the runbook states plainly that ALT-1/2/4 are activated-by-an-operator artifacts. |
| 2026-06-27 | **Batch 3 (Backups & DR drill) SHIPPED — BAK-1..5.** Version-matched dump tooling (`scripts/backup/pg_backup.sh`+`pg_restore.sh`, `backend/Dockerfile.backup` `FROM postgres:15-alpine` + pinned static `mc`; local mode skips S3) → a *tested* local restore drill asserting row-count parity (`scripts/backup/drill.sh`, non-destructive scratch DB) → a prod-overlay-only nightly `CronJob` (`k8s/overlays/prod/backup-cronjob.yaml`, CI publishes `openshiksha-backup`) → a `BackupRun` freshness gauge (`openshiksha_backup_age_seconds`) on the MET-2 collector → `docs/ops/backups.md` runbook. | [#474](https://github.com/openshiksha/openshiksha/pull/474)–[#477](https://github.com/openshiksha/openshiksha/pull/477) + this PR | Two ops lessons. (1) **kustomize's security boundary** forbids an overlay referencing a file *outside* its own dir, so the prod-only CronJob lives in `overlays/prod/`, not `base/` — prod-only placement is both the workaround and the intent (qa/dev never run it). (2) A freshness gauge must treat **empty history honestly**: no successful `BackupRun` ⇒ *omit* `openshiksha_backup_age_seconds` (don't emit `0`), so a total backup outage can't masquerade as "0 seconds old". Version-matched `pg_dump` (image pinned to the server's major) is non-negotiable — an older client refuses a newer server. |
