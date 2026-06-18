# MPN-1 — PushSubscription model + VAPID config + dependency

**Date:** 2026-06-17
**Initiative:** Mobile Shell & PWA-Offline → web-push later-phase
**Classification:** New

## Summary

Lays the backend foundation for **web push due-date reminders** — the
mobile-native notification channel that reaches a student's home-screen PWA
install even when the app is closed. This PR is fully additive and ships dark:
the model and config exist, but no endpoints are wired and nothing sends yet
(that's MPN-2/MPN-5).

## What changed

- **`PushSubscription` model** (`core/models.py`): `user` FK
  (`related_name="push_subscriptions"`, CASCADE), `endpoint` (`URLField`,
  `unique=True`), `p256dh` + `auth` client keys, optional `user_agent`,
  `created_at`. The unique endpoint makes re-subscribing from the same browser
  an upsert (implemented in MPN-2) rather than a duplicate.
- **Migration** `core/0029_pushsubscription.py`.
- **VAPID settings** (`settings/base.py`): `VAPID_PUBLIC_KEY`,
  `VAPID_PRIVATE_KEY`, `VAPID_ADMIN_EMAIL`, all read from env and **blank-safe**
  — dev/CI without keys simply disable push (the API will return an empty public
  key and the frontend hides the affordance) instead of erroring.
- **Dependency**: `pywebpush==2.0.3` (its native crypto rides Django's existing
  `cryptography` transitive dep — no new wheel pain).
- **Admin**: `PushSubscriptionAdmin` with read-only keys.

## Legacy reference

Legacy OpenShiksha had **email-only** notifications and no PWA / service worker /
push of any kind. Web push is net-new capability, not a port. The reminder
*cadence/eligibility* logic (`send_due_date_reminders`) is preserved and reused
in MPN-5 so the email and push channels can never drift.

## Tests

`core/tests/test_push_subscription_model.py` — create, `__str__` truncation,
unique-endpoint `IntegrityError`, cascade-delete with user. All pass.

## Migration notes

Additive table only; no changes to existing tables. Safe to apply on `qa`/prod.

## Next steps

MPN-2 (subscribe/unsubscribe API + `send_web_push` helper) builds directly on
this model.
