# OBS-4 — Request-correlation id + JSON log option

## Summary
Adds a `RequestIDMiddleware` that stamps every request with a correlation id
(from an incoming `X-Request-ID` header, or a fresh uuid4), threads it through all
log records via a `ContextVar`, echoes it back on the response, and tags the
Sentry scope when Sentry is active. Adds an opt-in JSON log formatter selected by
`LOG_FORMAT=json`. The default text logging is untouched (no behaviour change).

## Classification
Improve.

## Legacy files referenced
None — the monolith had no request correlation (failures were diagnosed by SSH +
`grep` over flat, uncorrelated logs). Correlation is the improvement over both
legacy and today's modern stack.

## What changed
- **`backend/openshiksha/apps/core/request_context.py`** (new) — a `ContextVar`
  (thread- *and* asyncio-task-isolated, correct under Daphne/ASGI) with
  `get/set/reset_request_id` helpers.
- **`backend/openshiksha/apps/core/middleware.py`** (new) — `RequestIDMiddleware`:
  reads/generates the id, sets `request.request_id`, stores it in the contextvar
  (reset in a `finally` so it never leaks across requests on a reused worker),
  echoes `X-Request-ID` on the response, and tags the Sentry scope **iff Sentry is
  active** (guarded soft-dep on OBS-3 — no-op when sentry-sdk is absent).
- **`backend/openshiksha/apps/core/logging_utils.py`** (new) — `RequestIDFilter`
  (injects `record.request_id`, default `"-"`) + `JSONFormatter` (one JSON object
  per line: `level/time/logger/message/request_id`, plus `exc_info` when present).
- **`backend/openshiksha/settings/base.py`** —
  - `RequestIDMiddleware` added right after `SecurityMiddleware`.
  - `LOGGING`: registered the `request_id` filter on both handlers, added the
    `json` formatter, and select it via `LOG_FORMAT=json` (default `text` →
    today's `simple`/`verbose` formatters, byte-for-byte unchanged).

## Tests written
`backend/openshiksha/apps/core/tests/test_request_id.py` (8 tests, all green):
- middleware round-trips a supplied `X-Request-ID`; generates a 32-char uuid4 hex
  when absent; the response always carries the header; the contextvar resets to
  `"-"` between requests.
- `request_context` set/get/reset round-trip.
- `RequestIDFilter` injects the id; `JSONFormatter` emits parseable JSON
  containing `request_id` (and defaults it to `"-"`).

Full backend suite re-run green (**1096 passed**) — the global middleware causes
no regressions.

## Migration notes
None — no model changes.

## How to verify
- `pytest openshiksha/apps/core/tests/test_request_id.py` (8 pass).
- `curl -i :8000/healthz/` → response has an `X-Request-ID` header; supplying one
  echoes it back.
- Run with `LOG_FORMAT=json` → console/file logs become one JSON object per line
  with a `request_id` field.

## Next steps
OBS-5 (frontend error reporting via the shared `ErrorBoundary`, env-gated).
