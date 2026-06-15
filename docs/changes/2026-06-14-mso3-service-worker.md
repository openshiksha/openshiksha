# MSO-3 — Service worker via vite-plugin-pwa

**Date:** 2026-06-14
**Classification:** New
**Initiative:** Mobile Shell & PWA-Offline (Batch 1, PR 3)

## Summary

Add a Workbox service worker (via `vite-plugin-pwa`) that precaches the built app
shell so a cold launch with no network still renders the React app, plus runtime
caches for the Google Fonts + KaTeX CDNs (text/math render offline) and an
explicit `NetworkOnly` rule for `/api`. Registration is prod-only; a slim "new
version available" banner prompts a refresh when a new build is waiting.

## Legacy reference

None — Django 1.11 was server-rendered/online-only. New SPA capability.

## What changed

- **`frontend_modern/vite.config.ts`** — added the `VitePWA` plugin with:
  - `registerType: 'autoUpdate'`, `injectRegister: null` (we register manually,
    prod-only, in `PwaUpdater`), `manifest: false` (we ship a hand-written
    `manifest.webmanifest` in MSO-1 — never emit a second one),
    `devOptions.enabled: false` (no SW in dev).
  - `workbox.globPatterns` precaches `js/css/html/svg/png/ico/woff/woff2`.
  - `navigateFallback: 'index.html'` with `navigateFallbackDenylist: [/^\/api/]`
    so deep links boot offline but `/api` never gets the shell.
  - `runtimeCaching`: `fonts.gstatic.com` + `cdn.jsdelivr.net/npm/katex` as
    `CacheFirst` (year-long expiry); `/api/*` as explicit `NetworkOnly`
    (principle 2 — the persisted React Query cache in MSO-4, not Workbox, owns
    API read-tolerance).
  - Test alias mapping `virtual:pwa-register/react` → a stub so importing
    `PwaUpdater`/`App` under Vitest resolves cleanly.
- **`frontend_modern/src/features/pwa/UpdateBanner.tsx`** (new) — presentational
  slim banner (brand orange, `role="status"`, `aria-live="polite"`) with a
  Refresh button; localized `pwa.updateAvailable` / `pwa.refresh`.
- **`frontend_modern/src/features/pwa/PwaUpdater.tsx`** (new) — uses
  `useRegisterSW` from `virtual:pwa-register/react`; renders `UpdateBanner` when
  `needRefresh`, wiring Refresh to `updateServiceWorker(true)`.
- **`frontend_modern/src/test-stubs/pwa-register-react.ts`** (new) — inert hook
  stub for the build-time virtual module.
- **`frontend_modern/src/App.tsx`** — mount `<PwaUpdater />` inside `I18nProvider`.
- **`frontend_modern/src/vite-env.d.ts`** — `/// <reference types="vite-plugin-pwa/client" />`.
- **i18n** — `pwa.updateAvailable` / `pwa.refresh` in en/hi (complete) + mr (pilot).
- **deps** — `vite-plugin-pwa@^1.3.0` (dev dep; pulls Workbox 7).

## Technical details

- The SW (`sw.js`) and Workbox runtime (`workbox-*.js`) are emitted as **separate**
  files, not folded into the entry chunk. The entry chunk only gains the small
  registration glue (~2 kB), staying well under the 160 kB budget (139 kB).
- `autoUpdate` + Workbox precache hashing means a new build busts stale precache
  entries and fires `needRefresh`, so the prompt shows on redeploy.

## Tests

- `UpdateBanner.test.tsx` (2) — polite status role + Refresh calls back.
- Full gate: `tsc --noEmit` clean, `lint` clean, `vitest run` 404 passing,
  `npm run build` emits `sw.js` + `workbox-*.js` (92 precache entries), bundle
  budget green (139 kB vs 160 kB).
- SW runtime behavior validated manually (steps in MSO-5's offline-test doc):
  build → serve `dist/` → load once → DevTools Offline → reload → shell renders.

## Migration notes

None — frontend-only, additive. New dev dependency only.

## Next steps

- MSO-4: persist the React Query cache to IndexedDB so the precached shell (this
  PR) can boot offline *and* read the last-fetched assignments.
- MSO-5: `beforeinstallprompt` install affordance + the manual offline-test doc.
