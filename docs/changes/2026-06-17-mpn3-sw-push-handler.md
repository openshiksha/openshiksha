# MPN-3 — Service worker push + notificationclick handler

**Date:** 2026-06-17
**Initiative:** Mobile Shell & PWA-Offline → web-push later-phase
**Classification:** New
**Independent** — no dependency on MPN-1/MPN-2.

## Summary

Adds the client-side half of web push: the service worker now renders an OS
notification when a push arrives and deep-links to the right page when the user
taps it. Layered onto the existing generated SW (MSO-3) with zero change to the
precache strategy.

## What changed

- **`public/push-handler.js`** — two listeners:
  - `push`: parses the JSON payload (`{title, body, url, tag}`) and calls
    `showNotification` with the 192 icon (used for both icon and badge until a
    dedicated monochrome badge asset is added), tagging by assignment id so
    duplicate reminders collapse. Falls back gracefully if the payload isn't
    JSON.
  - `notificationclick`: closes the toast, then focuses an open tab whose URL
    matches the deep link, or opens a new window.
- **`vite.config.ts`** — `workbox.importScripts: ['push-handler.js']`. This
  pulls the handler into the **generateSW** output; we deliberately did **not**
  switch to `injectManifest`, so all MSO-3 precache/runtime-cache behavior is
  untouched.

## Tests / verification

- `scripts/check-push-handler.test.mjs` (4 checks): file present, both
  listeners registered, `showNotification` + deep-link present, and
  `importScripts` references it in `vite.config.ts`.
- `npm run build` confirmed: built `dist/sw.js` contains
  `importScripts("push-handler.js")` and the file is precached.
- Entry chunk unchanged at **146 kB** (< 160 kB CI budget) — the handler is a
  separate precached file, not in the entry bundle.
- `type-check` + `lint` clean.

## Notes

- Dev has the SW disabled (`devOptions.enabled: false`), so push must be tested
  against a prod build / preview (captured in the MPN-5 manual-test doc).

## Next steps

MPN-4 adds the frontend opt-in (`usePushSubscription`) that registers a
subscription so this handler has something to receive.
