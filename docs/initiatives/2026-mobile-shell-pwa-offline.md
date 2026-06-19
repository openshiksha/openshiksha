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

### Batch 2 (shipped 2026-06-15 — `docs/daily-plans/2026-06-15-plan.md`) — offline write-tolerance ✅

- **MSO-6 — Replay-safe / idempotent submission writes (backend).** Make the
  submission write path safe to replay: a re-submit of an already-submitted
  submission is a no-op returning the existing score; a stale post-submit auto-save
  is dropped; grading only fires on the ungraded→graded transition (`score is None`
  gate) — closes a latent re-grade hazard in the `post_save` signal. **Improve.**
- **MSO-7 — Offline mutation queue foundation.** Keyed `setMutationDefaults` +
  `networkMode: 'offlineFirst'`, persist **paused** submission mutations to the
  Batch 1 IndexedDB persister (flip `shouldDehydrateMutation` to an allowlist), and
  `resumePausedMutations()` on reconnect. No new dependency. **New.**
- **MSO-8 — "Saved offline · will sync" status UX.** Localized, `aria-live`
  indicator driven by `useMutationState` + `useOnlineStatus`; global pending-sync
  count. **New.**
- **MSO-9 — Offline final-submit.** Optimistic "submitted — will be graded when back
  online" state; the queued submit replays onto the MSO-6-hardened endpoint and the
  real score reconciles on success. **New.**
- **MSO-10 — Batch 2 close-out.** Manual offline-write test doc + ledger + STATUS.
  **Docs.**

### Later phases

- ~~**Route-level mobile layouts:** per-route mobile-first layouts beyond the
  shared shell, where dense teacher tables still overflow on phones.~~ **SHIPPED
  2026-06-18 (Batch 4, RML-1..5, #382–#385)** — see ledger below.
- ~~**Push notifications:** due-date reminders as web push.~~ **SHIPPED 2026-06-17
  (Batch 3, MPN-1..5, #375–#379)** — see ledger below.

**Both later phases are now shipped. With the first-phase DoD met (Batch 1), this
initiative is complete.**

## Ledger

_(append one row per merged PR)_

| PR | Increment | Notes |
|---|---|---|
| #358 | MSO-1 | `manifest.webmanifest` + 192/512 any + maskable icons (paper bg, 20% safe-zone) from the orange logo; `index.html` manifest link + `apple-touch-icon` → 192; `check-manifest.test.mjs` validity + icon-exists guard |
| #359 | MSO-2 | `useOnlineStatus()` hook + slim warm-amber `OfflineBanner` (`aria-live`) in `AppShell`; localized `connectivity.*` (en/hi/mr) |
| #360 | MSO-3 | `vite-plugin-pwa` SW: precache shell, `CacheFirst` fonts/KaTeX, `/api` `NetworkOnly`, navigateFallback; prod-only manual registration; localized "new version" `UpdateBanner`; SW emitted as separate files (entry chunk unchanged) |
| #361 | MSO-4 | `PersistQueryClientProvider` + `idb-keyval` persister; reads-only dehydrate allowlist (student core-loop keys; never auth/PII/mutations); `buster` keyed to a cache version; `gcTime` 24h |
| #362 | MSO-5 | `useInstallPrompt` (module-level `beforeinstallprompt` capture) + dismissible `InstallBanner` (localized `pwa.install*`); manual offline-test checklist; batch close-out |
| #367 | MSO-6 | Replay-safe / idempotent submission writes: `SubmissionSerializer.update()` no-op on already-submitted (closes the async double-grade race) + `validate()` 200-not-400 on replay; signal `score is None` grade gate. **Improve** |
| #368 | MSO-7 | Offline mutation queue: keyed `setMutationDefaults` (`networkMode: 'offlineFirst'`, rehydration-safe `mutationFn`/`onSuccess`) + paused-submission persist allowlist + `resumePausedMutations()` on restore. No new dep. **New** |
| #369 | MSO-8 | "Saved offline · will sync" UX: `useSyncState`/`usePendingSyncCount` over `useMutationState`; `SyncStatus` inline indicator + `PendingSyncBadge`; honest copy; `sync.*` i18n (en/hi). **New** |
| #370 | MSO-9 | Offline final-submit: optimistic "will be graded when back online" card (no fake score), queued submit replays onto MSO-6 and the real score reconciles; `onError` re-opens the form. **New** |
| #375 | MPN-1 | `PushSubscription` model (unique endpoint, p256dh/auth keys) + migration 0029 + `pywebpush` dep + blank-safe VAPID settings + admin. Ships dark. **New** |
| #376 | MPN-2 | `core.push.send_web_push` (stale 404/410 prune, blank-key no-op, never raises) + `GET /push/vapid-public-key/`, `POST /push/subscribe/` (upsert by endpoint), `POST /push/unsubscribe/`. **New** |
| #377 | MPN-3 | `public/push-handler.js` (`push` → showNotification, `notificationclick` → deep-link) layered via `workbox.importScripts` on the generateSW output; SW-presence guard. Entry chunk unchanged. **New** |
| #379 | MPN-4 | `usePushSubscription` hook (key-gated supported, requestPermission → subscribe → POST) + dismissible `PushBanner` + ProfilePage toggle + `push.*` i18n (en/hi). **New** |
| #378 | MPN-5 | `send_due_date_reminders` fans web push alongside email (one opt-out governs both; eligibility broadened to email OR push; deep-link url + collapse tag); `emails.build_due_reminder_push` localized copy. Manual-test doc. **Improve** |
| #382 | RML-1 | `shared/ui/ResponsiveTable` primitive — real `<table>` at `sm:`+, stacked label/value card list below `sm:` from one `columns`/`rows` def; repo `hidden sm:table` / `sm:hidden` dual-render (no `matchMedia`). First consumer: `ClassHealthPanel` (drops `overflow-x-auto` + `min-w-[22rem]`). On `/design`. Entry chunk unchanged. **New** |
| #383 | RML-2 | `TeacherAssignmentDetailPage` submissions `<table>` → `ResponsiveTable`; opportunistically localized the page's hardcoded English (it had slipped LA-6) — `teacher.ad*` keys in en+hi, dates via `useFormat()`. **Improve** |
| #384 | RML-3 | `CreateQuestionPage` fixed grids → mobile-first: AI panel `grid-cols-3` → `grid-cols-1 sm:grid-cols-3`, chapter `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`; subpart tab buttons `min-h-[44px]` touch target. Presentation only. **Improve** |
| #385 | RML-4 | `OpenResponseGradingPage` review-form row `flex-wrap` → `flex-col sm:flex-row`; marks input `w-full sm:w-24`, comment `sm:min-w-[12rem]`; response blockquote `break-words`. AI-suggest/finalise flow untouched. **Improve** |

**Batch 4 shipped 2026-06-18** — route-level mobile layouts. The dense teacher
surfaces that still overflowed horizontally on a phone (Class Health and
Assignment-detail submissions tables, the Create-Question multi-column grids, and
the Open-Response grading form) are now readable and usable on a 360 px screen with
no horizontal scroll — via a small reusable `ResponsiveTable` primitive (RML-1) and
per-surface mobile-first stacking. RML-2 also folded the assignment-detail page back
into the LA i18n registry (en+hi) while it was open. The **"route-level mobile
layouts" later-phase item is shipped**; manual test in
`docs/perf/2026-06-18-mobile-layouts-manual-test.md`. **With this batch, both later
phases and the first-phase DoD are done — the Mobile Shell & PWA-Offline initiative
is complete.**

**Batch 3 shipped 2026-06-17** — web push due-date reminders. A student who
installs OpenShiksha to their home screen can opt in (banner / ProfilePage
toggle) and receive a due-date reminder as a native phone notification — even
with the app closed — reusing MSO-3's service worker and the existing
`send_due_date_reminders` task. Email stays the source of truth; push is an
additive channel that never fails the reminder run. The **"web push" later-phase
item is shipped**; manual test in `docs/perf/2026-06-17-pwa-push-manual-test.md`.

**Batch 2 shipped 2026-06-15** — the student core loop is now write-tolerant
offline. A student on a dropped connection keeps answering (auto-saves queue
durably to IndexedDB), can submit (optimistic "will be graded when back online"),
and every queued write replays **exactly once** — without double-grading — when
the network returns (server hardened idempotent in MSO-6). The **"Offline
write-tolerance" later-phase item is shipped.** See the manual offline-*write*
test checklist in `docs/perf/2026-06-15-pwa-offline-write-manual-test.md`
(sibling to Batch 1's `docs/perf/2026-06-14-pwa-offline-manual-test.md`).

**Batch 1 shipped 2026-06-14** — OpenShiksha is now an installable PWA whose
student core loop survives a flaky/absent connection: precached shell boots
offline, persisted query cache makes loaded assignments readable offline, an
honest localized offline banner shows throughout, and supported browsers offer
an "Add to home screen" affordance. See the manual offline-test checklist in
`docs/perf/2026-06-14-pwa-offline-manual-test.md`.
