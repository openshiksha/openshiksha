import { test, expect, type ConsoleMessage } from '@playwright/test';

// GSV-2b — golden-path e2e smoke for the AI-Native Interactive Learning
// Phase-2 step-solver widget (Beat 7).
//
// The story: a student solves an equation one line at a time; the in-sandbox
// deterministic engine (GSV-2a, a port of the backend GSV-1 algebra engine —
// never AI) lights each line ✓/✗ **live**, and the student's final line is
// reported through the existing per-subpart grader. The Vitest suite
// (`src/widgets/step-solver/index.test.ts`) covers the executed-render
// behaviour against happy-dom AND the anti-drift parity with `algebra.ts`.
//
// What jsdom CANNOT cover is the part that only exists in a real browser: the
// `sandbox="allow-scripts"` iframe actually rendering the widget, the student
// typing into it, the live ✓/✗ updating per keystroke, and the final answer
// crossing the postMessage boundary back to the host — the exact value the
// per-subpart grader scores. That render → interact → grade-signal tail is what
// silently regresses (sandbox attrs, the host bridge, the protocol) and never
// shows up in a unit test. This spec nails it down, and stays backend-free (it
// drives the public `/widgets/dev` playground under `vite preview`).
//
// It also captures the demo screenshot reproducibly: the PNG referenced from
// docs/demo/golden-path.md is regenerated every run, so it can never go stale
// relative to the code.
test.describe('step-solver — render → live ✓/✗ → grade signal', () => {
  // A two-line solve of 2x + 1 = 7: subtract 1 (→ 2x = 6), divide by 2 (→ x = 3).
  // Each line is algebraically equivalent to the one above, so both light ✓.
  const STEP_SOLVER_CONFIG = '{ "prompt": "2x + 1 = 7", "label": "Solve for x, one step per line" }';

  test('a student solves an equation line by line and the final answer reaches the host', async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    const response = await page.goto('/widgets/dev?kind=step-solver');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    // Drop in the prompt config. The preview remounts on config change.
    await page.getByLabel('Config JSON').fill(STEP_SOLVER_CONFIG);

    // The widget renders inside the sandboxed iframe (sandbox="allow-scripts",
    // deliberately no allow-same-origin). Playwright drives it at the browser
    // protocol level, so it crosses the boundary scripts cannot.
    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const firstStep = widgetFrame.getByLabel('Step 1');
    await expect(firstStep, 'the step-solver should render in the sandbox').toBeVisible();

    // Before any interaction the widget reports nothing — a question can be left
    // blank (no reportValue-on-mount). The host panel proves it.
    await expect(page.getByText('No value reported yet.')).toBeVisible();

    // Line 1: subtract 1 from both sides → still equivalent → live ✓.
    await firstStep.fill('2x = 6');
    await expect(
      widgetFrame.getByText('✓', { exact: true }).first(),
      'an equivalent first step lights ✓ live',
    ).toBeVisible();

    // Enter commits the line and opens the next step row.
    await firstStep.press('Enter');

    // Line 2: divide by 2 → the solution → live ✓ again.
    const secondStep = widgetFrame.getByLabel('Step 2');
    await expect(secondStep).toBeVisible();
    await secondStep.fill('x = 3');

    // Both committed steps should be ✓ (two green checks visible).
    await expect(widgetFrame.getByText('✓', { exact: true })).toHaveCount(2);

    // The grade signal: the host received the student's final line across the
    // postMessage boundary. This is the value the deterministic per-subpart
    // grader scores against `correct_answer`. The live ✓/✗ engine never touched
    // it, and AI is nowhere in this widget at all.
    await expect(page.locator('pre'), 'host should receive the final line "x = 3"').toHaveText(
      '"x = 3"',
    );

    // Capture the demo screenshot reproducibly straight into the committed
    // golden-path asset, so the PNG in the docs can never drift from the code.
    await page.screenshot({
      path: '../docs/demo/assets/gsv2b-step-solver.png',
      fullPage: true,
    });

    expect(
      consoleErrors,
      `console errors during the runtime smoke:\n${consoleErrors.join('\n')}`,
    ).toEqual([]);
  });

  test('a wrong step lights ✗ live, but is still reported (grade is deterministic + external)', async ({
    page,
  }) => {
    const response = await page.goto('/widgets/dev?kind=step-solver');
    expect(response?.ok()).toBeTruthy();
    await page.getByLabel('Config JSON').fill(STEP_SOLVER_CONFIG);

    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const firstStep = widgetFrame.getByLabel('Step 1');
    await expect(firstStep).toBeVisible();

    // 2x = 8 is NOT a valid step from 2x + 1 = 7 (it changes the solution) → ✗.
    await firstStep.fill('2x = 8');
    await expect(
      widgetFrame.getByText('✗', { exact: true }),
      'a non-equivalent step lights ✗ live',
    ).toBeVisible();

    // The widget still reports the line — correctness is graded by the
    // deterministic per-subpart grader, never the live marker.
    await expect(page.locator('pre')).toHaveText('"2x = 8"');
  });
});
