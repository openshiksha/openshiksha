# MSO-1 — Web App Manifest + maskable icons + installability

**Date:** 2026-06-14
**Classification:** New
**Initiative:** Mobile Shell & PWA-Offline (Batch 1, PR 1)

## Summary

Add the first PWA layer: a hand-written `manifest.webmanifest`, a full set of
192/512 "any" + maskable icons generated from the brand logo, and the
`index.html` wiring so browsers recognise OpenShiksha as an installable app. This
is the foundation the later batch items build on (the service worker in MSO-3
makes it actually installable; the install prompt in MSO-5 needs the manifest).

## Legacy reference

None — the Django 1.11 app was server-rendered and online-only. There is nothing
to port; PWA installability is a new capability the modern SPA makes possible.

## What changed

- **`frontend_modern/public/manifest.webmanifest`** (new) — `name`, `short_name`,
  `description`, `start_url`/`scope` `/`, `display: standalone`, `orientation:
  portrait`, `theme_color #FF6F00` (brand orange) and `background_color #FFF8F1`
  (the V2 `paper-50` token, confirmed in `tailwind.config`), `lang: en`, and four
  icons.
- **`frontend_modern/public/icons/`** (new) — `icon-192.png`, `icon-512.png`
  (`any` purpose, logo on the paper background) and `maskable-192.png`,
  `maskable-512.png` (logo scaled into the centre 60% so there is ≥20% safe-zone
  padding on each side; Android's circle/squircle mask won't clip the mark).
  Generated one-off from `public/brand/logo-orange.png` via `sharp` — the dep was
  **not** added to `package.json` (icons are committed PNGs, no runtime image dep).
- **`frontend_modern/index.html`** — added
  `<link rel="manifest" href="/manifest.webmanifest" />` and repointed
  `apple-touch-icon` from the raw 512 logo to `/icons/icon-192.png` for crispness.
  The existing `theme-color #FF6F00` and responsive viewport are unchanged.
- **`frontend_modern/scripts/check-manifest.test.mjs`** (new) — vitest guard
  asserting the manifest is valid JSON with the required installability fields,
  ships 192+512 icons in both `any` and `maskable` purposes, and that every
  referenced icon file actually exists on disk (no manifest → 404).

## Technical details

- Icon background uses `#FFF8F1` (paper-50) flattened so the transparent logo
  reads correctly on both light and dark home screens.
- The validity test lives in `scripts/` as `.mjs` (like `check-bundle-budget`) so
  it can read `public/` from disk without pulling `@types/node` into the
  DOM-only `src` tsconfig; vitest's `include` already covers `scripts/**/*.test.mjs`.

## Tests

- `scripts/check-manifest.test.mjs` — 4 tests, all passing.
- `npx tsc --noEmit` clean, `npm run lint` clean, `npm run build` succeeds;
  `manifest.webmanifest` + all four icons emit into `dist/`; bundle-budget guard
  still green (entry 137 kB vs 160 kB ceiling — manifest/icons are static assets,
  not bundled).

## Migration notes

None — frontend-only, additive.

## Next steps

- MSO-2: network-status hook + offline banner.
- MSO-3: `vite-plugin-pwa` service worker (precache shell) — makes the app
  actually installable (manifest + SW are both required).
- MSO-5: `beforeinstallprompt` capture + install affordance (depends on this).
