import { test, expect, type ConsoleMessage, type Route } from '@playwright/test';

// PV-4 — golden-path e2e smoke for the AI-Native Interactive Learning Phase-3
// propose-and-verify practice bank (Beat 14).
//
// The story (Phase 3): a teacher types a topic → the AI *proposes* a
// `number-line` `{widget_config, correct_answer}` (PV-2) → Beat-11's
// deterministic `verify_widget_problem` **gates the proposal server-side** so the
// answer is provably reachable on the widget → the verified pair renders in the
// live sandbox preview with the answer in hand (PV-3) → a **student** picks up
// that exact widget and reaches precisely the verified answer, which is the value
// the deterministic per-subpart grader scores. **AI proposed the problem; the
// engine proved it answerable; the AI never graded it.**
//
// The Vitest suites cover the head of this chain against jsdom + mocked network:
// the hook passthrough (`usePracticeProblem.test.ts`), the panel's verified-pill /
// answer / provenance / snap-adjusted-flag rendering (`PracticeProblemPanel.test.tsx`),
// and the dev-page wiring (`WidgetDevPage.test.tsx`).
//
// What jsdom CANNOT cover is the part that only exists in a real browser: the
// `sandbox="allow-scripts"` iframe actually rendering the verified problem, a
// student manipulating it, and the widget snapping to *exactly* the verified
// answer that the grader marks against `correct_answer`. That render → interact →
// reach-the-verified-answer tail is the on-screen payoff of "AI proposes, the
// engine disposes", and it is exactly what silently regresses (sandbox attrs, the
// host bridge, the number-line snap) and never shows up in a unit test.
//
// It stays **backend-free** (the playwright CI job only boots `vite preview`): it
// drives the public `/widgets/dev` playground and **stubs the PV-2 endpoint** with
// `page.route`, exactly the verified `{widget_config, correct_answer}` shape PV-2
// returns (the real proposer + its PV-1 gate + fallback are pinned by the 22
// backend pytest tests). The e2e proves the browser-only tail: the verified
// problem renders in the real sandbox and the student reaches the shown answer.
//
// It also captures the demo screenshot reproducibly: the PNG referenced from
// docs/demo/golden-path.md is regenerated every run, so it can never drift.

// The exact verified pair PV-2 returns for "mark 1/2 on a number line from 0 to
// 1": axis [0,1], step 0.5, so ½ is the single exact tick right of the origin.
// (Halves, not quarters, so the reachable answer is exact — the number-line's
// snap rounds step 0.25 to one decimal and would report 0.8 for ¾, the Beat-3
// quirk PV-1 is built to catch; here we assert an exact grade signal.)
const VERIFIED_PROBLEM = {
  widget_kind: 'number-line',
  widget_config: { min: 0, max: 1, step: 0.5, label: 'Mark 1/2 on the number line' },
  correct_answer: { answer: 0.5 },
  model_used: 'claude-opus-4-8',
  ai_available: true,
  repaired: false,
  verdict_code: 'reachable',
};

// The deterministic fallback PV-2 returns when the cascade is exhausted / a
// proposal is unsalvageable: the known-good, PV-1-passed safe problem, with
// `model_used: 'stub'` (→ neutral `Auto-problem` badge) and `ai_available: false`.
const SAFE_DEFAULT_PROBLEM = {
  widget_kind: 'number-line',
  widget_config: { min: 0, max: 1, step: 0.5, label: 'Mark 1/2 on the number line' },
  correct_answer: { answer: 0.5 },
  model_used: 'stub',
  ai_available: false,
  repaired: false,
  verdict_code: 'safe_default',
};

// Stub the PV-2 endpoint with the given verified problem shape. Keeps the spec
// backend-free while driving the real panel → hook → render path end to end.
async function stubPracticeProblem(
  page: import('@playwright/test').Page,
  body: unknown,
): Promise<void> {
  await page.route('**/ai/practice-problem/', (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    }),
  );
}

test.describe('propose-and-verify practice problem — verified render → student reaches the answer', () => {
  test('a verified AI problem renders and a student reaches exactly the shown answer', async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    await stubPracticeProblem(page, VERIFIED_PROBLEM);

    // The playground is public and backend-free; the "Generate a practice
    // problem" card is always wired in (it authors its own number-line).
    const response = await page.goto('/widgets/dev');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    // Teacher types the topic and asks for a problem. The PV-2 call is stubbed
    // above with the exact verified shape the real endpoint returns.
    await page.getByLabel('Topic').fill('mark 1/2 on a number line from 0 to 1');
    await page.getByRole('button', { name: /generate & verify/i }).click();

    // Honest provenance + the PV-1 guarantee, on screen: a real proposal wears
    // the ✨ AI-generated badge and the "✓ Verified answerable" pill — the AI
    // never got to decide correctness.
    await expect(page.getByText('✨ AI-generated')).toBeVisible();
    await expect(page.getByText('✓ Verified answerable')).toBeVisible();

    // The answer the engine proved reachable is shown in hand.
    await expect(page.getByText('Answer:').locator('..').getByText('0.5')).toBeVisible();

    // The verified problem renders in the SAME sandboxed iframe a hand-picked
    // widget uses (sandbox="allow-scripts", deliberately no allow-same-origin).
    // It is the last such iframe on the page — the panel renders after the main
    // preview. Playwright drives it below the same-origin boundary scripts can't
    // cross.
    const panelFrame = page
      .locator('iframe[title="Interactive question widget"]')
      .last()
      .contentFrame();
    const slider = panelFrame.getByRole('slider');
    await expect(slider, 'the verified problem should render in the sandbox').toBeVisible();

    // Student interaction: click to focus, anchor with Home (→ min, 0), step
    // once right with ArrowRight (→ +step, 0.5 = ½) — deterministic regardless
    // of where the click landed.
    await slider.click();
    await slider.press('Home');
    await slider.press('ArrowRight');

    // The payoff: the student reaches EXACTLY the verified answer the panel
    // showed (0.5). The widget's own live readout and its aria-valuenow both
    // report 0.5 — the value the deterministic grader marks against
    // `correct_answer`. The engine proved this value reachable *before* it
    // rendered; the student just reached it. AI proposed; it never graded.
    await expect(
      panelFrame.locator('.nl-readout strong'),
      'the student reaches the verified answer 0.5 on the widget',
    ).toHaveText('0.5');
    await expect(slider).toHaveAttribute('aria-valuenow', '0.5');

    // Capture the demo screenshot reproducibly into the committed golden-path
    // asset, so the PNG in the docs can never drift from the code.
    await page.screenshot({
      path: '../docs/demo/assets/pv4-practice-problem.png',
      fullPage: true,
    });

    // The whole runtime path must be clean — a console error here usually means
    // the sandbox bridge or the widget threw.
    expect(
      consoleErrors,
      `console errors during the runtime smoke:\n${consoleErrors.join('\n')}`,
    ).toEqual([]);
  });

  test('the deterministic fallback shows a verified safe problem, honestly labelled', async ({
    page,
  }) => {
    // No key / unsalvageable proposal → PV-2 returns the known-good safe problem
    // with model_used:'stub'. The panel must show it honestly: a neutral
    // Auto-problem badge + an "AI unavailable" line, never a stub dressed as a
    // real generation — and it is STILL verified answerable (the fallback rides
    // the same PV-1 gate).
    await stubPracticeProblem(page, SAFE_DEFAULT_PROBLEM);

    const response = await page.goto('/widgets/dev');
    expect(response?.ok()).toBeTruthy();

    await page.getByLabel('Topic').fill('anything at all');
    await page.getByRole('button', { name: /generate & verify/i }).click();

    // Honest provenance: neutral Auto-problem badge, no ✨ AI-generated, plus the
    // friendly unavailable line.
    await expect(page.getByText('Auto-problem')).toBeVisible();
    await expect(page.getByText('✨ AI-generated')).toHaveCount(0);
    await expect(page.getByText(/AI proposer is unavailable/i)).toBeVisible();

    // The fallback is still verified answerable and still renders a real,
    // interactive widget — the deterministic path is a working result, not a
    // dead end.
    await expect(page.getByText('✓ Verified answerable')).toBeVisible();
    const panelFrame = page
      .locator('iframe[title="Interactive question widget"]')
      .last()
      .contentFrame();
    await expect(
      panelFrame.getByRole('slider'),
      'the safe fallback problem still renders in the sandbox',
    ).toBeVisible();
  });
});
