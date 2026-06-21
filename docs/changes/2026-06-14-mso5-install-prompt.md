# MSO-5 — A2HS install prompt + Batch 1 close-out

**Date:** 2026-06-14
**Classification:** New / docs
**Initiative:** Mobile Shell & PWA-Offline (Batch 1, PR 5 — close-out)

## Summary

Add the "Add to home screen" affordance — capture `beforeinstallprompt`, show a
dismissible install banner on supported browsers — and close out Batch 1 with a
manual offline-test checklist, the ledger, and a STATUS headline update.

## Legacy reference

None — Django 1.11 was server-rendered/online-only. New SPA capability.

## What changed

- **`frontend_modern/src/features/pwa/useInstallPrompt.ts`** (new) — registers a
  **module-level** `beforeinstallprompt` listener (the event fires before React
  mounts, so a component effect would miss it), buffers the deferred event, and
  exposes `{ canInstall, promptInstall, dismiss }` via `useSyncExternalStore`.
  Tracks `appinstalled` to hide the affordance, and persists dismissal in
  `localStorage` (`os-install-dismissed`). iOS Safari never fires the event, so
  `canInstall` stays false there (we don't fake it).
- **`frontend_modern/src/features/pwa/InstallBanner.tsx`** (new) — slim,
  dismissible banner (not a modal) shown only when `canInstall`; localized
  `pwa.install*` copy, brand-orange Install button, ✕ to dismiss.
- **`frontend_modern/src/features/layout/AppShell.tsx`** — render
  `<InstallBanner />` between `<Navbar />` and `<main>`.
- **i18n** — `pwa.installPrompt` / `pwa.install` / `pwa.installDismiss` in en/hi
  (complete) + mr (pilot). Parity guard green.
- **`docs/perf/2026-06-14-pwa-offline-manual-test.md`** (new) — the manual
  checklist covering manifest/installability, offline shell boot, offline-readable
  assignments, the update prompt, the install prompt, and localisation.
- **Close-out** — initiative ledger filled with all five Batch 1 PRs + a
  "Batch 1 shipped" note; STATUS.md headline updated.

## Technical details

- Module-level event capture + `useSyncExternalStore` means any component can read
  a consistent install state regardless of mount timing, and multiple banners
  would stay in sync.
- The snapshot is a derived boolean so `useSyncExternalStore` doesn't loop.

## Tests

- `InstallBanner.test.tsx` (4) — hidden until `beforeinstallprompt` fires; appears
  after; Install calls the stashed event's `prompt()`; ✕ persists dismissal in
  `localStorage` and hides the banner.
- Full gate: `tsc --noEmit` clean, `lint` clean, `vitest run` 406 passing,
  `npm run build` ok, bundle budget green (139 kB vs 160 kB).

## Migration notes

None — frontend/docs only, additive.

## Next steps

- Initiative next phase: offline **write**-tolerance (queue + replay
  submissions/auto-saves on reconnect — needs an idempotency story against the
  grader); route-level mobile layouts for dense teacher tables; web push for
  due-date reminders.
