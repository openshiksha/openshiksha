# ALT-2 — Alertmanager config + ntfy bridge

**Date:** 2026-06-28
**Initiative:** Production Observability & Operational Readiness — Batch 4 (Uptime & alerting)
**Classification:** New

## Summary

Routes the ALT-1 alerts to a channel the team already uses (**ntfy**, already
wired for build notifications) with two artifacts:

- `docs/ops/alertmanager/alertmanager.yml` — a minimal Alertmanager config: a
  `route` grouped by `alertname`/`severity` with conservative
  `group_wait`/`repeat_interval`, to a single `webhook_configs` receiver pointed
  at the bridge. A commented `email_configs` block shows the e-mail alternative.
  No secrets in the file (the ntfy URL is injected via the bridge's env).
- `scripts/ops/alert_to_ntfy.py` — a ~self-contained **stdlib** bridge
  (`http.server` + `urllib.request`, **no new pip dependency**) that accepts an
  Alertmanager webhook POST on `/alert` and POSTs a **single-line** message to
  `ALERT_NTFY_URL` with `Title`/`Tags`/`Priority` headers derived from `severity`.

## Why a bridge

ntfy is not a native Alertmanager receiver — Alertmanager POSTs its own webhook
JSON schema, ntfy wants a plain-text body + headers. The ~60-line bridge is the
standard glue, and because the payload→`(title, body, headers)` mapping is
factored into the pure `format_alert` / `format_payload` functions, it is
trivially unit-testable. That is what makes this "tested config," not just YAML.

## Mapping

| severity | priority | tag |
|---|---|---|
| critical (firing) | high | rotating_light |
| warning (firing) | default | warning |
| info (firing) | low | information_source |
| **any (resolved)** | min | white_check_mark |

Resolved notifications are forced to `min` priority regardless of original
severity — the bad thing stopped, so it must not page. Bodies are collapsed to a
single line (the project notification convention).

## Tests

`scripts/ops/tests/test_alert_to_ntfy.py` (7 tests, **no network** — the HTTP POST
is the only seam, the formatter is pure):

- critical/firing → high + rotating_light + `[FIRING]` title
- warning/firing → default + warning
- resolved critical → min + white_check_mark + `[RESOLVED]` (does not page)
- multi-line summary collapses to one line
- summary → description → alertname body fallback chain
- unknown severity defaults safely (default/bell)
- multi-alert + empty payloads

Result: **7 passed**. `python -m py_compile scripts/ops/alert_to_ntfy.py` clean.

These run in CI via the ALT-4 `alerting-lint` job (the backend Test job only
collects `backend/` tests); `amtool check-config` also runs there.

## Security

The ntfy URL is read from `ALERT_NTFY_URL` and **never** echoed to logs (a leaked
topic URL is a write capability to the channel). The bridge stays a single stdlib
file, documented as a sidecar/one-off — not a new always-on dependency.

## Next steps

- ALT-3 adds the standalone uptime probe (alerts with zero Prometheus stack).
- ALT-4 adds `amtool check-config` + this pytest to CI.
- ALT-5 documents the routing path in `docs/ops/alerting.md`.
