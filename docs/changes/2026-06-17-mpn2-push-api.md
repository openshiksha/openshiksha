# MPN-2 — Subscribe/unsubscribe API + send_web_push helper

**Date:** 2026-06-17
**Initiative:** Mobile Shell & PWA-Offline → web-push later-phase
**Classification:** New
**Depends on:** MPN-1 (PushSubscription model)

## Summary

Wires the `PushSubscription` model (MPN-1) to the frontend with three DRF
endpoints and adds the server-side delivery helper that the due-date reminder
task will call in MPN-5. Backend-only; still ships dark until MPN-4/MPN-5.

## What changed

- **`core/push.py` — `send_web_push(user, payload) -> int`**: fans out an
  encrypted Web Push to every one of a user's subscriptions. Returns the count
  sent. Key behaviours:
  - **No-op without VAPID** — returns 0 when `VAPID_PRIVATE_KEY` is blank, so
    push is purely additive.
  - **Self-pruning** — a `404`/`410` from the push service deletes that stale
    subscription row; transient errors (e.g. 500) are logged and kept.
  - **Never raises into the caller** — each send is wrapped per-subscription so
    one dead endpoint can't abort a reminder fan-out.
  - `pywebpush` is imported lazily so the dep is only touched when push is on.
- **Endpoints** (`api/views/push.py`, wired in `api/urls.py`):
  - `GET /api/v1/push/vapid-public-key/` (AllowAny) → `{"publicKey": ...}`;
    empty string ⇒ frontend hides the affordance.
  - `POST /api/v1/push/subscribe/` (auth) → upsert by `endpoint`, scoped to
    `request.user`; 201 on create, 200 on update. Captures `user_agent`.
  - `POST /api/v1/push/unsubscribe/` (auth) → deletes the caller's row for the
    given endpoint only.

## Tests

`api/tests/test_push_api.py` (11 tests): subscribe create/idempotency, key
validation, auth gate, unsubscribe, vapid-key passthrough, and `send_web_push`
stale-prune (410) / transient-keep (500) / blank-key no-op (pywebpush mocked).

## Migration notes

None — no model changes.

## Next steps

MPN-4 consumes these endpoints from the frontend; MPN-5 calls `send_web_push`
from the due-date reminder task.
