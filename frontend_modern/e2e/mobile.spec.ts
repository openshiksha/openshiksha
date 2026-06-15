import { test, expect, devices, type ConsoleMessage } from '@playwright/test';

// Mobile-form-factor smoke for the public surfaces.
//
// Context (2026-06-14): the **Mobile Shell & PWA-Offline** initiative is the
// active top bet (docs/initiatives/2026-mobile-shell-pwa-offline.md).
// OpenShiksha targets K-12 students in India on phones, but every e2e project
// so far runs only `Desktop Chrome` — so a layout that quietly breaks at phone
// width (the single most common mobile regression) sails through CI green.
//
// This spec emulates a real handset (Pixel 5: 393×851, DPR 2.75, touch, mobile
// UA) and guards the two cheapest, highest-signal mobile failures on the
// public, backend-free routes:
//
//   1. **Horizontal overflow** — content wider than the viewport forces an
//      ugly left/right scroll and is almost always an unconstrained element
//      (a fixed width, an un-wrapped fl/grid row, an image without max-width).
//   2. **Console / page errors** — a paint that throws on mobile but not
//      desktop (e.g. a `matchMedia`/`ResizeObserver` path) would otherwise be
//      invisible to the desktop smoke.
//
// Only public routes that render their first paint without an API call are
// covered — same scope contract as visual.spec.ts. Authenticated mobile chrome
// (the M5-01 bottom tabs, the upcoming MSO-2 offline banner) needs the Docker
// stack and belongs to a future backend-attached project in
// playwright.config.ts.

// Emulate a representative Android handset for this file only. This overrides
// the config's single `Desktop Chrome` project without adding a second project
// (which would re-run every other spec at phone width for no benefit).
test.use({ ...devices['Pixel 5'] });

// A 1px slack absorbs sub-pixel rounding of scrollWidth vs. the layout
// viewport; anything wider is a genuine overflow.
const OVERFLOW_SLACK = 1;

interface PublicRoute {
  /** Human-readable name for the test title. */
  name: string;
  /** Route to navigate to. */
  path: string;
  /** A locator that, once visible, indicates the page has painted. */
  ready: string;
}

const PUBLIC_ROUTES: PublicRoute[] = [
  { name: 'home', path: '/', ready: 'h1' },
  { name: 'login', path: '/login', ready: 'h1' },
  { name: 'enquire', path: '/enquire', ready: 'h1' },
  { name: 'design showcase', path: '/design', ready: 'h1' },
];

test.describe('mobile smoke — public surfaces (Pixel 5)', () => {
  for (const route of PUBLIC_ROUTES) {
    test(`${route.name} paints with no overflow or console errors`, async ({ page }) => {
      const consoleErrors: string[] = [];
      page.on('console', (msg: ConsoleMessage) => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
      });
      page.on('pageerror', (err) => consoleErrors.push(err.message));

      const response = await page.goto(route.path);
      expect(response?.ok(), `GET ${route.path} should return 2xx`).toBeTruthy();

      await expect(page.locator(route.ready).first()).toBeVisible();
      // Let webfonts settle so a late-loading glyph can't widen the layout
      // after we measure.
      await page.evaluate(() => document.fonts.ready);

      const overflow = await page.evaluate(() => {
        const doc = document.documentElement;
        return {
          scrollWidth: doc.scrollWidth,
          clientWidth: doc.clientWidth,
        };
      });
      expect(
        overflow.scrollWidth,
        `${route.path} overflows horizontally at phone width ` +
          `(scrollWidth ${overflow.scrollWidth} > clientWidth ${overflow.clientWidth})`,
      ).toBeLessThanOrEqual(overflow.clientWidth + OVERFLOW_SLACK);

      expect(
        consoleErrors,
        `console errors on ${route.path} (mobile):\n${consoleErrors.join('\n')}`,
      ).toEqual([]);
    });
  }
});
