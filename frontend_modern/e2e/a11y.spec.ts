import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
import { AUTH_SETUP } from './support/auth';

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
// (reporting mode).
//
// A11Y-5 flips the **genuinely-clean** public routes to `gate: true`. A route is
// only gated once its CTA renders disabled at load (so axe scans it) *or* its
// brand surfaces compute clean — i.e. axe has zero `violations`. Routes whose
// primary `.btn-brand` is **enabled at load** (e.g. the HomePage hero) currently
// land their white-on-`brand-600` contrast failure in axe's `incomplete` bucket
// (axe can't always compute the background), so they stay reporting-mode until
// the systemic brand-button contrast is remediated (a design-shade decision —
// see the initiative doc / A11Y-4). The spec therefore also records `incomplete`
// so that masked risk is visible in the CI artifact instead of looking "clean".
// `/design` additionally renders deliberate edge cases (low-contrast swatches,
// sandboxed widget iframes) so it stays reporting-mode too.
interface AuditRoute {
  name: string;
  path: string;
  gate: boolean;
  // A11Y-6/9: when set, seed a JWT for the given role + stub the core-loop API
  // before navigating so `ProtectedRoute` admits the page and it renders content.
  auth?: 'student' | 'teacher' | 'parent';
}

const ROUTES: AuditRoute[] = [
  // Auth/enquiry forms: primary CTA is disabled until valid input, so the
  // enabled brand-button contrast question never renders at load → axe-clean →
  // safe to gate now.
  { name: 'login', path: '/login', gate: true },
  { name: 'register', path: '/register', gate: true },
  { name: 'register-school', path: '/register/school', gate: true },
  { name: 'register-open', path: '/register/open', gate: true },
  { name: 'enquire', path: '/enquire', gate: true },
  // A11Y-4 landed: `.btn-brand` repainted to `bg-brand-700` (#C05300, ≥4.5:1
  // white) so the enabled hero CTA now clears AA — `/` is gated.
  { name: 'home', path: '/', gate: true },
  // Deliberate showcase edge cases + widget iframes → reporting-mode.
  { name: 'design', path: '/design', gate: false },
  // A11Y-8: authenticated student core-loop — now GATED. The A11Y-6 baseline
  // came back structurally clean (zero label/landmark/heading violations) and
  // the one blocking colour-contrast finding (StreakBadge labels) was fixed in
  // A11Y-7 (#420), on top of A11Y-4's brand-shade token sweep (#417). With
  // `blocking === []` on all four routes, they flip to `gate: true` so a future
  // regression on the student core loop fails CI. Residual colour-contrast lands
  // in axe's `incomplete` bucket (background axe can't compute) — recorded but
  // non-gating, the same contract as the public routes.
  { name: 'student-dashboard', path: '/student', gate: true, auth: 'student' },
  { name: 'assignment-detail', path: '/student/assignments/1', gate: true, auth: 'student' },
  { name: 'proficiency', path: '/student/proficiency', gate: true, auth: 'student' },
  { name: 'srs-drill', path: '/student/srs-drill/1', gate: true, auth: 'student' },
  // A11Y-12 (Batch 3): authenticated teacher + parent core surfaces — now GATED.
  // The A11Y-9 baseline found the teacher surfaces structurally clean and the one
  // blocking finding on /parent (small brand-700 text on the brand-50 tint) was
  // fixed in A11Y-11. All four compute `blocking === []`, so they gate against
  // future regressions. Residual colour-contrast stays in axe's `incomplete`
  // bucket (non-gating), the same contract as the public + student routes.
  { name: 'teacher-dashboard', path: '/teacher', gate: true, auth: 'teacher' },
  { name: 'teacher-question-bank', path: '/teacher/questions', gate: true, auth: 'teacher' },
  { name: 'teacher-grading', path: '/teacher/grading', gate: true, auth: 'teacher' },
  { name: 'parent-dashboard', path: '/parent', gate: true, auth: 'parent' },
  // A11Y-13/15 (Batch 3 close-out): the dense teacher authoring forms + parent
  // insights — the last authenticated surfaces that were still UNMEASURED — now
  // GATED. The A11Y-13 baseline came back structurally clean (`blocking === []`
  // on all five): the forms are composed from the shared labelled `Input` /
  // `Select` / `Textarea` primitives, so the labelling/heading findings A11Y-14
  // anticipated never materialised (the planned remediation surface was empty,
  // mirroring how A11Y-9 found the teacher *core* surfaces clean). Residual
  // colour-contrast lands in axe's `incomplete` bucket (background axe can't
  // compute) — recorded but non-gating, the same contract as every other route.
  // This fully satisfies the initiative's DoD item 6.
  { name: 'teacher-create-question', path: '/teacher/questions/new', gate: true, auth: 'teacher' },
  { name: 'teacher-create-assignment', path: '/teacher/assignments/new', gate: true, auth: 'teacher' },
  { name: 'teacher-create-problemset', path: '/teacher/problem-sets/new', gate: true, auth: 'teacher' },
  { name: 'parent-insights', path: '/parent/insights', gate: true, auth: 'parent' },
  { name: 'parent-insights-child', path: '/parent/insights/10', gate: true, auth: 'parent' },
];

const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

test.describe('public surfaces — accessibility (axe-core)', () => {
  for (const route of ROUTES) {
    test(`${route.name} (${route.path})`, async ({ page }, testInfo) => {
      if (route.auth) await AUTH_SETUP[route.auth](page);
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
        // `incomplete` = checks axe could not decide automatically (most often
        // colour-contrast over a background it can't read). Recorded so masked
        // risk — e.g. the enabled brand-button contrast — is visible rather than
        // hidden behind a zero-violations summary. Does not affect the gate.
        incomplete: results.incomplete.map((v) => ({
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
