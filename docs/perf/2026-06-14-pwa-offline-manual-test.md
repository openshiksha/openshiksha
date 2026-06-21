# PWA / Offline — manual test checklist

**Initiative:** Mobile Shell & PWA-Offline (Batch 1, 2026-06-14)

The service worker (MSO-3), persisted cache (MSO-4) and install prompt (MSO-5)
can't be fully exercised by Vitest (no real SW / IndexedDB / `beforeinstallprompt`
in happy-dom). Run this checklist against a production build before relying on
offline behaviour.

## Setup

```bash
cd frontend_modern
npm run build
npm run preview   # serves dist/ on http://localhost:4173 (HTTPS/localhost = SW-eligible)
```

Open the preview URL in Chrome or Edge. The SW only registers in a **production**
build (`import.meta.env.PROD`), never in `npm run dev`.

## 1. Manifest + installability (MSO-1 + MSO-3)

- [ ] DevTools → Application → **Manifest** parses with no errors; lists all four
      icons; the maskable preview shows the logo uncropped inside the safe zone.
- [ ] DevTools → Application → **Service Workers** shows `sw.js` activated.
- [ ] The browser offers **Install** (omnibox install icon / ⋮ → "Install
      OpenShiksha…"). Installing launches it standalone (no browser chrome).

## 2. Offline app-shell boot (MSO-3)

- [ ] Load the app once online (so the SW precaches the shell).
- [ ] DevTools → Network → **Offline**, then reload. The React shell still renders
      (not the browser's dead-dino page).
- [ ] A deep link (e.g. `/student/assignments/123`) also boots offline via the
      `index.html` navigateFallback.

## 3. Offline-readable assignments (MSO-4 + MSO-2)

- [ ] While online, open a student assignment so its questions load.
- [ ] Go **Offline** (DevTools) and reload. The warm-amber **offline banner**
      appears, and every question still renders from the persisted React Query
      cache.
- [ ] DevTools → Application → IndexedDB shows the `os-react-query-cache` entry;
      it contains assignment/dashboard reads but **no** `auth` or mutation data.
- [ ] Go back online → the banner disappears.

## 4. Update prompt (MSO-3)

- [ ] Rebuild (`npm run build`) and reload the installed/preview app. The slim
      brand-orange **"new version available — Refresh"** banner appears; clicking
      Refresh activates the new SW and reloads.

## 5. Install prompt (MSO-5)

- [ ] On a fresh profile (clear `localStorage`), the **"Add to home screen"**
      banner appears once the browser fires `beforeinstallprompt`.
- [ ] Clicking **Install** triggers the native prompt; **✕** dismisses it and it
      stays gone (persisted in `localStorage` under `os-install-dismissed`).
- [ ] On iOS Safari nothing is shown (no `beforeinstallprompt` — we don't fake it).

## 6. Localisation (MSO-2 + MSO-5)

- [ ] Switch language to हिंदी / मराठी and repeat 3 + 5: the offline banner and
      install copy render localized.
