import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';

// Accessibility baseline for the /design showcase.
//
// /design is the living catalog for every V2 "Chalk & Unlock" primitive
// (docs/initiatives/2026-design-system-v2.md). Running axe-core here gives
// us a stable place to measure a11y health as the design system grows.
//
// **Reporting mode (not gating).** A full WCAG 2.1 AA pass is a planned
// future initiative (see docs/initiatives/STATUS.md backlog). Until that
// initiative starts, this spec only records violations: it writes a JSON
// summary to `axe-report/design.json` (uploaded as a CI artifact alongside
// the Playwright HTML report) and logs counts to the test output. It does
// not fail on findings — flip `FAIL_ON_BLOCKING` to `true` once the AA pass
// begins and the known showcase noise (intentional low-contrast swatches,
// sandboxed widget iframe) has been triaged.
const FAIL_ON_BLOCKING = false;

test.describe('/design — accessibility (axe-core baseline)', () => {
  test('records axe-core violations', async ({ page }, testInfo) => {
    await page.goto('/design');
    await expect(page.locator('h1').first()).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    const byImpact: Record<string, number> = {};
    for (const v of results.violations) {
      const key = v.impact ?? 'unknown';
      byImpact[key] = (byImpact[key] ?? 0) + 1;
    }
    const blocking = results.violations.filter(
      (v) => v.impact === 'serious' || v.impact === 'critical',
    );

    const summary = {
      url: '/design',
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
      path.join(reportDir, 'design.json'),
      JSON.stringify({ summary, violations: results.violations }, null, 2),
    );

    console.log('[axe] /design summary:', JSON.stringify(summary, null, 2));

    if (FAIL_ON_BLOCKING) {
      expect(
        blocking,
        `axe-core blocking violations on /design:\n${JSON.stringify(summary.blocking, null, 2)}`,
      ).toEqual([]);
    }
  });
});
