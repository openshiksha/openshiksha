# Mobile Shell & PWA-Offline

> **Promoted 2026-06-14** as the new top active initiative. Language Access
> (i18n en/हिं/मरा) closed its North Star with LA-9; only LA-10 (authored-content
> translation) remains and is blocked on product design. The named next bet on
> the [STATUS board](STATUS.md) was **Mobile shell / PWA-offline** — this doc
> promotes it.

## North Star

**OpenShiksha installs to a phone home screen and the student core loop survives a
flaky or absent connection.** A K-12 student in India on patchy 3G should be able
to (1) add OpenShiksha to their home screen and launch it full-screen like a
native app, and (2) re-open an assignment they already loaded, read its questions,
and keep working when the network drops — instead of seeing a white screen or a
spinner that never resolves.

This is mission-core for the target market: intermittent connectivity is the norm,
not the exception, and an installable PWA removes the app-store barrier entirely.

## Why now

- **Mobile shell is already partly built.** M5-01 shipped a role-aware bottom tab
  bar; the V2 overhaul (M1–M7) shipped safe-area padding, large touch targets, an
  account drawer, and a responsive surface audit. The chrome is mobile-ready — what
  is missing is **installability** and **offline tolerance**.
- **PWA-offline is fully greenfield.** Verified 2026-06-14: no web app manifest,
  no service worker, no `navigator.onLine` handling anywhere in `src/`, and the
  React Query cache is in-memory only (lost on reload). Every increment below is
  additive.
- **The performance budget protects this.** The entry chunk sits at ~41 kB gzip
  against a 160 kB CI guard. A Workbox service worker is a *separate* file the
  browser registers out-of-band, and the IndexedDB persister (`idb-keyval`) is
  ~1 kB — so offline support costs the entry budget essentially nothing.

## Principles

1. **Read-tolerance before write-tolerance.** Ship offline *reading* (re-open a
   loaded assignment, read questions) first. Offline *writing* (queue+replay
   submissions) is a later, higher-risk phase — do not bundle it into the first
   batch.
2. **Never cache `/api` writes or auth.** The service worker handles static app-
   shell assets only; API GETs are served by the React Query persisted cache, not
   Workbox. Mutations and auth are always NetworkOnly. Never persist JWTs into the
   query cache.
3. **The app shell must boot offline.** Precache the built JS/CSS/HTML so a cold
   launch with no network still renders the React app (which then reads the
   persisted query cache), rather than the browser's dead-dino page.
4. **Honest offline UX.** When offline, tell the user plainly ("You're offline —
   showing saved work") with an `aria-live` status, localized in en/हिं/मराठी.
   Never silently show stale data as if it were live.
5. **Defend the budget.** Every PWA PR runs `npm run build` and confirms the entry
   chunk is unchanged against the 160 kB guard; the SW and persister live outside
   the entry chunk.

## Definition of Done (first phase)

- [ ] Installable: valid web app manifest + maskable icons; Chrome/Edge offer
      "Install app"; launches standalone (no browser chrome).
- [ ] App shell boots with the network disabled (service worker precache).
- [ ] A student who loaded an assignment online can re-open it offline and read
      every question (persisted React Query cache + precached shell).
- [ ] Clear, localized offline indicator; "new version available" refresh prompt.
- [ ] A dismissible "Add to home screen" affordance on supported browsers.
- [ ] Entry-chunk budget unchanged; SW + persister live outside it.

## Backlog

### Batch 1 (planned 2026-06-14 — `docs/daily-plans/2026-06-14-plan.md`)

- **MSO-1 — Web App Manifest + maskable icons + installability.** Manifest,
  192/512 + maskable icons from the orange logo, `index.html` wiring. **New.**
- **MSO-2 — Network-status hook + offline banner.** `useOnlineStatus()` +
  `OfflineBanner` in `AppShell`, localized. **New.**
- **MSO-3 — Service worker (vite-plugin-pwa).** Precache app shell, runtime caches
  for fonts/KaTeX, prod-only registration, update prompt. **New.**
- **MSO-4 — Persist React Query cache to IndexedDB.** Offline-readable assignments
  + dashboard via `persistQueryClient` + `idb-keyval`. **New.**
- **MSO-5 — A2HS install prompt + batch close-out.** `beforeinstallprompt` capture
  + dismissible install affordance; ledger + manual offline-test doc. **New/docs.**

### Later phases (not yet scoped)

- **Offline write-tolerance:** queue assignment auto-saves / submissions made
  offline and replay on reconnect (background sync). Higher risk — needs a
  conflict/idempotency story against the grader. Separate batch.
- **Route-level mobile layouts:** per-route mobile-first layouts beyond the shared
  shell, where dense teacher tables still overflow on phones.
- **Push notifications:** due-date reminders as web push (the email reminder
  already exists; web push is the mobile-native channel).

## Ledger

_(append one row per merged PR)_

| PR | Increment | Notes |
|---|---|---|
| MSO-1 | MSO-1 | `manifest.webmanifest` + 192/512 any + maskable icons (paper bg, 20% safe-zone) from the orange logo; `index.html` manifest link + `apple-touch-icon` → 192; `scripts/check-manifest.test.mjs` validity + icon-exists guard |
