# MPN-4 — Frontend push opt-in + settings toggle

**Date:** 2026-06-17
**Initiative:** Mobile Shell & PWA-Offline → web-push later-phase
**Classification:** New
**Depends on:** MPN-2 (subscribe API + vapid-public-key) and MPN-3 (SW handler).

## Summary

The user-facing half of web push: a student can now opt in to push reminders
and the subscription is registered with the backend. Completes the loop —
MPN-3's SW handler now has something to receive, MPN-5's reminder task has
someone to deliver to.

## What changed

- **`features/pwa/usePushSubscription.ts`** — the bridge hook:
  - Fetches the server VAPID public key (`GET /push/vapid-public-key/`). An
    empty key (push not configured) ⇒ `supported = false` and the UI hides.
  - `subscribe()`: `Notification.requestPermission()` → `pushManager.subscribe`
    with the decoded VAPID key → `POST /push/subscribe/` with the browser's
    serialized subscription (`toJSON()` → `{endpoint, keys}`).
  - `unsubscribe()`: `POST /push/unsubscribe/` (best-effort) then
    `subscription.unsubscribe()`.
  - Reflects any existing browser subscription into `isSubscribed`.
  - **Honest UX** (principle 4): degrades to hidden where push can't work — no
    browser support, no server key, or iOS Safari before the PWA is installed.
- **`features/pwa/PushBanner.tsx`** — dismissible "Get reminders on your phone"
  banner mirroring the MSO-5 `InstallBanner`; rendered in `AppShell`. Shows only
  when `supported && !isSubscribed && permission !== 'denied' && !dismissed`.
- **`features/shared/ProfilePage.tsx`** — a **Push notifications** toggle next to
  the existing email-reminders control (subscribe/unsubscribe; shows a
  "blocked in browser" hint when permission is denied).
- **i18n** — `push.*` keys in `en` + `hi` (parity guard green).

## Tests / verification

- `usePushSubscription.test.ts` (6): `urlBase64ToUint8Array` decode; unsupported
  when key blank; supported with key; subscribe posts the serialized payload;
  subscribe aborts when permission not granted; existing-subscription reflect +
  unsubscribe clears.
- `PushBanner.test.tsx` (4): visible when eligible; hidden when unsupported /
  already subscribed / permission denied.
- Full suite **446 passed**; `type-check` + `lint` clean; build clean, entry
  chunk **149 kB** (< 160 kB budget).

## Next steps

Batch complete (MPN-1..5). Remaining initiative later-phase: route-level mobile
layouts.
