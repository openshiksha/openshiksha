import { test, expect } from '@playwright/test';

// Visual-regression baseline for V2 "Chalk & Unlock" public surfaces.
//
// Snapshots live next to this spec under `visual.spec.ts-snapshots/`. They
// are platform-suffixed by Playwright (e.g. `-chromium-linux.png`); the CI
// project runs only `chromium` on Linux, so checked-in baselines are CI's
// reference. To intentionally update a baseline after a design change run:
//
//     npm run test:e2e:update-snapshots
//
// Only **public, backend-free** routes are covered here. Login/Register/Enquire
// render their initial paint without an API call; we wait for a stable header
// element instead of network idle. Authenticated surfaces (dashboards) need
// the Docker stack and are out of scope until we add a backend-attached
// project to playwright.config.ts.
//
// `maxDiffPixelRatio` gives us a generous tolerance for sub-pixel font
// anti-aliasing differences across CI runners while still catching real
// layout regressions.
const DIFF_TOLERANCE = { maxDiffPixelRatio: 0.02 };

const DESKTOP = { width: 1280, height: 800 };
const MOBILE = { width: 375, height: 720 };

interface Surface {
  /** Snapshot file slug (no extension). */
  slug: string;
  /** Route to navigate to. */
  path: string;
  /** A locator that, once visible, indicates the page has painted. */
  ready: string;
}

const SURFACES: Surface[] = [
  // The living showcase — if any V2 primitive regresses, the diff lights up here.
  { slug: 'design', path: '/design', ready: 'h1' },
  // Marketing / first-impression chalkboard hero.
  { slug: 'home', path: '/', ready: 'h1' },
  // Auth flow — flagship of the chalkboard/paper layout.
  { slug: 'login', path: '/login', ready: 'h1' },
  // Public enquiry form (M3-03).
  { slug: 'enquire', path: '/enquire', ready: 'h1' },
];

// ACTIVE as of 2026-06-22. Baselines were generated inside the pinned
// Playwright Docker image (`mcr.microsoft.com/playwright:v1.61.0-noble`) and
// committed under `e2e/visual.spec.ts-snapshots/`. The CI `visual-regression`
// job runs *inside that same image*, so the snapshot environment is identical
// — this is what makes pixel comparisons reproducible (a bare ubuntu runner
// renders system fonts differently and would flake). These tests are tagged
// `@visual` so the bare-runner `frontend-e2e` job skips them (it runs
// `--grep-invert @visual`); only the container job runs `--grep @visual`.
//
// To refresh baselines after an intentional design change, regenerate them in
// the same image (see docs/changes/2026-06-22-visual-regression-activated.md)
// and commit the updated PNGs alongside the design change.
test.describe('visual regression — V2 public surfaces @visual', () => {
  for (const surface of SURFACES) {
    test(`${surface.slug} — desktop @visual`, async ({ page }) => {
      await page.setViewportSize(DESKTOP);
      await page.goto(surface.path);
      await expect(page.locator(surface.ready).first()).toBeVisible();
      // Let webfonts settle so character widths don't shift the layout.
      await page.evaluate(() => document.fonts.ready);
      await expect(page).toHaveScreenshot(`${surface.slug}-desktop.png`, DIFF_TOLERANCE);
    });

    test(`${surface.slug} — mobile (375) @visual`, async ({ page }) => {
      await page.setViewportSize(MOBILE);
      await page.goto(surface.path);
      await expect(page.locator(surface.ready).first()).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      await expect(page).toHaveScreenshot(`${surface.slug}-mobile.png`, DIFF_TOLERANCE);
    });
  }
});
