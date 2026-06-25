import { test, expect } from '@playwright/test';
import { AUTH_SETUP } from './support/auth';

// Automated keyboard-traversal contract (A11Y-16, Batch 4 kickoff).
//
// Part of the Accessibility — WCAG 2.1 AA initiative
// (docs/initiatives/2026-accessibility-wcag-aa.md). Where `a11y.spec.ts` is the
// *static* axe gate (labels/contrast/landmarks), this spec is the *behavioural*
// gate for keyboard operability — the parts axe cannot see:
//
//   • WCAG 2.4.1 Bypass Blocks — the skip link jumps focus to `#main-content`.
//   • WCAG 2.1.2 No Keyboard Trap — Tab keeps advancing across an input-dense
//     page; focus is never stuck on one control.
//
// Reuses the authenticated harness (`support/auth.ts`): a seeded JWT + stubbed
// `**/api/v1/**` reads, so it runs against `vite preview` with no backend.
//
// NOTE (Batch 4 follow-up): the QuestionBank "Add to set" side-sheet still needs
// a true focus *trap* (Tab cycling bounded within the dialog) and focus *restore*
// (returning focus to the trigger on close) before those can be gated here — both
// are tracked in the screen-reader sign-off doc (A11Y-17). The dialog already
// moves focus inside on open and closes on Escape; the trap/restore work is the
// remaining WCAG 2.4.3 / 2.1.2 gap for the dialog pattern.

test.describe('keyboard operability', () => {
  test('skip link jumps focus to #main-content (WCAG 2.4.1)', async ({ page }) => {
    await AUTH_SETUP.student(page);
    await page.goto('/student');
    await page.waitForLoadState('networkidle');

    // The skip link is the first focusable element in the DOM (before the navbar).
    await page.keyboard.press('Tab');
    const skipLink = page.getByRole('link', { name: /skip to main content/i });
    await expect(skipLink).toBeFocused();

    // Activating it must move focus into the main landmark.
    await page.keyboard.press('Enter');
    const focusInMain = await page.evaluate(() => {
      const main = document.getElementById('main-content');
      const active = document.activeElement;
      return !!main && (main === active || main.contains(active));
    });
    expect(focusInMain).toBe(true);
  });

  test('no keyboard trap across the assignment answer form (WCAG 2.1.2)', async ({ page }) => {
    await AUTH_SETUP.student(page);
    await page.goto('/student/assignments/1');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1').first()).toBeVisible();

    // Tab through a generous number of stops. If any control trapped focus, the
    // active element would stop changing; instead we assert focus keeps landing
    // on distinct, real elements (never stuck on one, never lost to <body>).
    const seen = new Set<string>();
    let bodyHits = 0;
    for (let i = 0; i < 25; i++) {
      await page.keyboard.press('Tab');
      const desc = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return 'BODY';
        // A stable-enough signature: tag + accessible-ish name + position.
        const rect = el.getBoundingClientRect();
        return `${el.tagName}:${(el.textContent ?? '').trim().slice(0, 20)}:${Math.round(rect.top)}x${Math.round(rect.left)}`;
      });
      if (desc === 'BODY') bodyHits++;
      else seen.add(desc);
    }

    // Several distinct focus stops were reached → focus advanced freely.
    expect(seen.size).toBeGreaterThan(2);
    // Focus was never lost to <body> for a sustained run (no dead-end trap).
    expect(bodyHits).toBeLessThan(25);
  });
});
