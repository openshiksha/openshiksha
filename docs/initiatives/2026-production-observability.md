# Production Observability & Operational Readiness

**Status:** 🟢 Active (promoted 2026-06-25) · **Owner:** `openshiksha-plan` / `openshiksha-execute` routines

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

## Later batches
- **Batch 2 — Metrics & dashboards. ✅ SHIPPED 2026-06-27** (MET-1..5,
  [#467](https://github.com/openshiksha/openshiksha/pull/467)–[#471](https://github.com/openshiksha/openshiksha/pull/471)):
  gated Prometheus `/metrics`, on-scrape business/queue-depth + `TaskResult`-derived
  Celery gauges, gated HTTP request metrics, Grafana starter + scrape runbook.
- **Batch 3 — Backups & DR drill** (next). Automated Postgres dump to object storage +
  a documented, *tested* restore runbook (the data-loss insurance the live DB
  currently lacks).
- **Batch 4 — Uptime & alerting.** External uptime check on `/healthz/` +
  `/readyz/`; alert routing (email/ntfy) on Sentry error-rate + probe-fail.
  a documented, *tested* restore runbook (the data-loss insurance the live DB
  currently lacks).
- **Batch 4 — Uptime & alerting.** External uptime check on `/healthz/` +
  `/readyz/`; alert routing (email/ntfy) on Sentry error-rate + probe-fail.

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
