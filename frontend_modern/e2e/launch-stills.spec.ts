import { test, expect, type ConsoleMessage } from '@playwright/test';

// T-2 (launch) — first-pass stills for the launch video shot list.
//
// Reuses the golden-path screenshot mechanics (see describe-to-build-grade and
// step-solver-grade specs): drive the public, backend-free `/widgets/dev`
// playground to the exact demo frame, then drop a PNG straight into
// `docs/launch/assets/` so the script can be judged against real frames without
// a manual dev-stack run. These are reference stills for framing/rehearsal —
// the final recording is captured live — so we frame the widget region rather
// than the whole playground chrome.
//
// Scope: only the two backend-free shots live here.
//   • Shot 1 — Describe-to-Build (number line, student marks ½ → host reads 0.5)
//   • Shot 5 — Step-solver (2x + 1 = 7 solved line by line, ✓/✓ → host reads x = 3)
// Shot 4 (student drags a point in a real assignment) needs the seeded full
// stack (auth + seed_demo_data); it is deferred to a stack-up QA pass — see the
// T-2 note in docs/launch/video-plan.md.

const ASSET_DIR = '../docs/launch/assets';

test.describe('launch stills — backend-free playground frames', () => {
  test('shot 1 — describe-to-build number line (student marks ½)', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    // Same axis/snap the DTB-2 endpoint emits for "mark one half": halves keep
    // the reported value exact (¾ would round to 0.8 on this grid).
    const NUMBER_LINE_CONFIG =
      '{ "min": 0, "max": 1, "step": 0.5, "label": "Mark 1/2 on the number line" }';

    const response = await page.goto('/widgets/dev?kind=number-line');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    await page.getByLabel('Config JSON').fill(NUMBER_LINE_CONFIG);

    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const slider = widgetFrame.getByRole('slider');
    await expect(slider, 'the number line should render in the sandbox').toBeVisible();

    // Anchor to min then step once right → ½ (0.5), independent of the click.
    await slider.click();
    await slider.press('Home');
    await slider.press('ArrowRight');
    await expect(page.locator('pre'), 'host should receive 0.5').toHaveText('0.5');

    await page.screenshot({ path: `${ASSET_DIR}/shot-01-describe-to-build.png`, fullPage: true });

    expect(consoleErrors, `console errors:\n${consoleErrors.join('\n')}`).toEqual([]);
  });

  test('shot 5 — step-solver live ✓/✓ (2x + 1 = 7 → x = 3)', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    const STEP_SOLVER_CONFIG =
      '{ "prompt": "2x + 1 = 7", "label": "Solve for x, one step per line" }';

    const response = await page.goto('/widgets/dev?kind=step-solver');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    await page.getByLabel('Config JSON').fill(STEP_SOLVER_CONFIG);

    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const firstStep = widgetFrame.getByLabel('Step 1');
    await expect(firstStep, 'the step-solver should render in the sandbox').toBeVisible();

    // Two equivalent lines both light ✓; the final answer crosses to the host.
    await firstStep.fill('2x = 6');
    await expect(
      widgetFrame.getByText('✓', { exact: true }).first(),
      'an equivalent first step lights ✓ live',
    ).toBeVisible();
    // Enter commits the line and opens the next step row.
    await firstStep.press('Enter');
    const secondStep = widgetFrame.getByLabel('Step 2');
    await expect(secondStep).toBeVisible();
    await secondStep.fill('x = 3');
    await expect(widgetFrame.getByText('✓', { exact: true })).toHaveCount(2);
    await expect(page.locator('pre'), 'host should receive the final line "x = 3"').toHaveText(
      '"x = 3"',
    );

    await page.screenshot({ path: `${ASSET_DIR}/shot-05-step-solver.png`, fullPage: true });

    expect(consoleErrors, `console errors:\n${consoleErrors.join('\n')}`).toEqual([]);
  });
});
