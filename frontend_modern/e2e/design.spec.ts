import { test, expect, type ConsoleMessage } from '@playwright/test';

// Smoke test for the living design-system showcase at /design.
//
// This is the only currently-public, backend-free route in the app, which
// makes it the right anchor for our first e2e test. The V2 "Chalk & Unlock"
// initiative (docs/initiatives/2026-design-system-v2.md) requires every new
// primitive to be added to this page — so if /design crashes, the whole
// design system has regressed and we want CI red.
test.describe('/design — design system showcase', () => {
  test('renders without console errors', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    const response = await page.goto('/design');
    expect(response?.ok(), 'GET /design should return 2xx').toBeTruthy();

    // The showcase always renders an h1 with the system name. If this changes,
    // update the assertion — but a missing h1 here usually means the page
    // bailed before mount.
    await expect(page.locator('h1').first()).toBeVisible();

    // Brand orange anchor should appear somewhere on the page — every
    // showcase build renders the token swatches.
    await expect(page.getByText('#FF6F00', { exact: false }).first()).toBeVisible();

    expect(consoleErrors, `console errors on /design:\n${consoleErrors.join('\n')}`).toEqual([]);
  });
});
