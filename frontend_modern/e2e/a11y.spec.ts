import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

// Per-route accessibility baseline (axe-core, WCAG 2.1 AA).
//
// Part of the Accessibility — WCAG 2.1 AA initiative
// (docs/initiatives/2026-accessibility-wcag-aa.md). Every unauthenticated
// surface gets its own axe scan; the result is written to
// `axe-report/<name>.json` (uploaded as a CI artifact alongside the Playwright
// HTML report) and the by-impact counts are logged to the test output.
//
// **Gating is per-route.** A route with `gate: true` asserts zero
// serious/critical (blocking) violations — turning CI's `frontend-e2e` job into
// a regression gate for that surface. A route with `gate: false` only records
// (reporting mode). Batch 1 (A11Y-1) lands every route in reporting mode to
// produce the fix inventory; A11Y-5 flips the cleaned public routes to
// `gate: true`. `/design` deliberately renders edge cases (intentional
// low-contrast swatches, sandboxed widget iframe) so it stays reporting-mode
// until that known noise is triaged/annotated.
interface AuditRoute {
  name: string;
  path: string;
  gate: boolean;
}

const ROUTES: AuditRoute[] = [
  { name: 'home', path: '/', gate: false },
  { name: 'login', path: '/login', gate: false },
  { name: 'register', path: '/register', gate: false },
  { name: 'register-school', path: '/register/school', gate: false },
  { name: 'register-open', path: '/register/open', gate: false },
  { name: 'enquire', path: '/enquire', gate: false },
  { name: 'design', path: '/design', gate: false },
];

const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

test.describe('public surfaces — accessibility (axe-core)', () => {
  for (const route of ROUTES) {
    test(`${route.name} (${route.path})`, async ({ page }, testInfo) => {
      await page.goto(route.path);
      // Settle async chrome (fonts, lazy chunks) before the scan so contrast
      // and structure are measured against the final rendered UI, and keep a
      // reporting spec from flaking on a slow paint.
      await page.waitForLoadState('networkidle');
      await page.evaluate(() => document.fonts.ready);
      await expect(page.locator('h1').first()).toBeVisible();

      const results = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();

      const byImpact: Record<string, number> = {};
      for (const v of results.violations) {
        const key = v.impact ?? 'unknown';
        byImpact[key] = (byImpact[key] ?? 0) + 1;
      }
      const blocking = results.violations.filter(
        (v) => v.impact === 'serious' || v.impact === 'critical',
      );

      const summary = {
        url: route.path,
        gate: route.gate,
        total: results.violations.length,
        byImpact,
        blocking: blocking.map((v) => ({
          id: v.id,
          impact: v.impact,
          help: v.help,
          nodes: v.nodes.length,
        })),
      };

      const reportDir = path.join(testInfo.project.outputDir, '..', 'axe-report');
      fs.mkdirSync(reportDir, { recursive: true });
      fs.writeFileSync(
        path.join(reportDir, `${route.name}.json`),
        JSON.stringify({ summary, violations: results.violations }, null, 2),
      );

      console.log(`[axe] ${route.path} summary:`, JSON.stringify(summary, null, 2));

      if (route.gate) {
        expect(
          blocking,
          `axe-core blocking violations on ${route.path}:\n${JSON.stringify(summary.blocking, null, 2)}`,
        ).toEqual([]);
      }
    });
  }
});
