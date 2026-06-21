# MSO-2 — Network-status hook + offline banner

**Date:** 2026-06-14
**Classification:** New
**Initiative:** Mobile Shell & PWA-Offline (Batch 1, PR 2)

## Summary

Give the app an honest, localized offline indicator. A `useOnlineStatus()` hook
tracks browser connectivity, and a slim `OfflineBanner` rendered in `AppShell`
appears (warm amber, `aria-live`) whenever the user is offline. Independent of
the service worker — lands on its own.

## Legacy reference

None — the Django 1.11 app was server-rendered/online-only; a dropped connection
just produced a dead page. This is a new modern-SPA capability.

## What changed

- **`frontend_modern/src/shared/hooks/useOnlineStatus.ts`** (new) — returns
  `navigator.onLine`, subscribes to `window` `online`/`offline`, cleans up on
  unmount. SSR/test-safe default (`true` when `navigator` is undefined). JSDoc
  documents the `navigator.onLine` optimism caveat: it's fine for a banner, but
  data fetching must **not** be gated on it (React Query owns fetch failures).
- **`frontend_modern/src/features/layout/OfflineBanner.tsx`** (new) — renders
  nothing when online; when offline shows a slim warm-amber banner
  (`role="status"` + `aria-live="polite"`) with an inline wifi-off SVG and the
  localized `connectivity.offlineBanner` copy.
- **`frontend_modern/src/features/layout/AppShell.tsx`** — render
  `<OfflineBanner />` between `<Navbar />` and `<main>`; skip-link target intact.
- **i18n** — new `connectivity.` cluster (`offlineTitle`, `offlineBanner`,
  `backOnline`) added to `en.ts` + `hi.ts` (complete locales) and `mr.ts` (pilot
  — translated since it's a core-loop string). Parity guard green.

## Tests

- `useOnlineStatus.test.ts` — mount reflects `navigator.onLine`; flips on
  `offline`/`online` events; unsubscribes listeners on unmount. (3)
- `OfflineBanner.test.tsx` — nothing when online; polite status banner when
  offline; appears/disappears across connectivity changes. (3)
- Full gate: `npx tsc --noEmit` clean, `npm run lint` clean, `npx vitest run`
  408 passing, `npm run build` ok, bundle budget green (138 kB vs 160 kB).

## Migration notes

None — frontend-only, additive.

## Next steps

- MSO-3: service worker so the precached shell can boot offline (then the banner
  shows over actually-usable saved content).
- MSO-5 reuses this slim-banner pattern for the "new version available" prompt.
