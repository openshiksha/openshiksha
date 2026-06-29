import { test, expect, type ConsoleMessage } from '@playwright/test';

// GSV-4b — golden-path e2e smoke for the AI-Native Interactive Learning
// Phase-2 step coach auto-feed (Beat 10).
//
// The story (GSV-4b): a student makes a slip *inside the network-less widget
// sandbox*; the deterministic in-sandbox engine lights it ✗ and the widget
// posts a typed `step` message across the trust boundary to the host. The host
// auto-feeds that exact wrong-step line pair to the host-side AI coach — no
// copy-paste — so the explanation is one click away on the very pair that went
// wrong. The AI stays outside the sandbox (principle 1) and outside the grade
// path (principle 2): `step` carries only the *deterministic* verdict.
//
// The Vitest suites cover the head of this chain against jsdom + mocked network:
// the protocol guard (`protocol.test.ts`), the host bridge dispatch
// (`host.test.ts`), the widget's committed-step emission
// (`step-solver/index.test.ts`), and the dev-page auto-feed wiring + provenance
// (`WidgetDevPage.test.tsx` / `StepHintPanel.test.tsx`).
//
// What jsdom CANNOT cover is the part that only exists in a real browser: the
// `sandbox="allow-scripts"` iframe actually rendering the widget, a student
// typing a wrong line into it, and the new `step` message crossing the
// postMessage boundary to drive the host coach. That sandbox→host wire is
// exactly what silently regresses (sandbox attrs, the host bridge, the protocol
// version) and never shows up in a unit test. This spec nails it down and stays
// backend-free (it drives the public `/widgets/dev` playground under `vite
// preview`; it asserts the auto-feed, not the AI call, which needs the backend).
//
// It also captures the demo screenshot reproducibly: the PNG referenced from
// docs/demo/golden-path.md is regenerated every run, so it can never drift.
test.describe('step coach auto-feed — wrong step in sandbox → host coach pair', () => {
  // Solve 2x + 3 = 7 (so x = 2; a valid first move is 2x = 4). The student
  // instead writes 2x = 10 — a non-equivalent step that changes the solution,
  // so the in-sandbox engine lights ✗ and the host coach should target it.
  const STEP_SOLVER_CONFIG =
    '{ "prompt": "2x + 3 = 7", "label": "Solve for x, one step per line" }';

  test('a wrong step committed in the widget auto-feeds the host coach', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    const response = await page.goto('/widgets/dev?kind=step-solver');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    await page.getByLabel('Config JSON').fill(STEP_SOLVER_CONFIG);

    // Before any slip, the coach shows the seeded manual pair and no auto-feed
    // affordance.
    await expect(page.getByText(/auto-filled from your last wrong step/i)).toHaveCount(0);

    // The widget renders inside the sandboxed iframe; Playwright drives it at
    // the browser-protocol level, crossing the boundary scripts cannot.
    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const firstStep = widgetFrame.getByLabel('Step 1');
    await expect(firstStep, 'the step-solver should render in the sandbox').toBeVisible();

    // Write a wrong line → the in-sandbox deterministic engine lights ✗ live.
    await firstStep.fill('2x = 10');
    await expect(
      widgetFrame.getByText('✗', { exact: true }),
      'a non-equivalent step lights ✗ live (deterministic, in-sandbox)',
    ).toBeVisible();

    // Enter commits the line → the widget posts the typed `step` message →
    // the host auto-feeds the exact wrong-step pair to the coach.
    await firstStep.press('Enter');

    // The grade-independent coach signal: the host received the wrong-step pair
    // across the postMessage boundary and routed it to the AI coach inputs.
    await expect(
      page.getByLabel('Previous line'),
      'the host coach "previous line" is auto-filled from the sandbox',
    ).toHaveValue('2x + 3 = 7');
    await expect(
      page.getByLabel('New line'),
      'the host coach "new line" is auto-filled from the sandbox',
    ).toHaveValue('2x = 10');
    await expect(
      page.getByText(/auto-filled from your last wrong step/i),
      'the auto-feed affordance appears for the student',
    ).toBeVisible();

    // Capture the demo screenshot reproducibly into the committed golden-path
    // asset, so the PNG in the docs can never drift from the code.
    await page.screenshot({
      path: '../docs/demo/assets/gsv4b-step-coach-autofeed.png',
      fullPage: true,
    });

    expect(
      consoleErrors,
      `console errors during the runtime smoke:\n${consoleErrors.join('\n')}`,
    ).toEqual([]);
  });

  test('a correct step does NOT auto-feed the coach (AI only ever sees wrong steps)', async ({
    page,
  }) => {
    const response = await page.goto('/widgets/dev?kind=step-solver');
    expect(response?.ok()).toBeTruthy();
    await page.getByLabel('Config JSON').fill(STEP_SOLVER_CONFIG);

    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const firstStep = widgetFrame.getByLabel('Step 1');
    await expect(firstStep).toBeVisible();

    // 2x = 4 is a valid move from 2x + 3 = 7 → ✓; committing it must NOT feed
    // the coach (the auto-feed affordance never appears).
    await firstStep.fill('2x = 4');
    await expect(widgetFrame.getByText('✓', { exact: true })).toBeVisible();
    await firstStep.press('Enter');

    await expect(page.getByText(/auto-filled from your last wrong step/i)).toHaveCount(0);
    // The seeded manual pair is untouched.
    await expect(page.getByLabel('New line')).toHaveValue('2x = 10');
  });
});
