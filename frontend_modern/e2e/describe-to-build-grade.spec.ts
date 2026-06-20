import { test, expect, type ConsoleMessage } from '@playwright/test';

// DTB-4 — golden-path e2e smoke for AI-Native Interactive Learning.
//
// The describe-to-build story is: a teacher types a sentence → the AI proposes a
// schema-valid `{widget_kind, widget_config}` (DTB-2) → it renders in the live
// sandbox preview (DTB-3) → a *student* interacts and the deterministic grader
// scores the value the widget reports. The `type → generate → render` head of
// that chain is covered by the Vitest suites (WidgetGalleryPanel + the
// useWidgetAuthoring hook, real proposal + fallback, against a mocked network).
//
// What those jsdom tests CANNOT cover is the part that only exists in a real
// browser: the *sandboxed iframe runtime* actually rendering the widget the AI
// described, the student manipulating it, and the answer value crossing the
// postMessage trust boundary back to the host — i.e. the value the per-subpart
// grader receives. That render → interact → grade-signal tail is exactly what
// silently regresses (sandbox attrs, the host bridge identity guard, the
// protocol) and never shows up in a unit test. This spec nails it down.
//
// It stays **backend-free** (the playwright CI job only boots `vite preview`):
// it drives the public `/widgets/dev` playground, which mounts the same
// `InteractiveWidget` host the teacher/student flows use, with the same
// `number-line` config the AI emits for *"a number line where students mark
// 3/4"*. The "Last reported value" panel is the literal grade signal — the host
// surfaces whatever the widget reported through the protocol, which is what the
// numeric grader marks against `correct_answer`.
//
// It also captures the demo screenshot reproducibly (no manual dev-stack run):
// the PNG dropped into docs/demo/golden-path.md is regenerated every time this
// spec runs, so it can never go stale relative to the code.
test.describe('describe-to-build — render → student interaction → grade signal', () => {
  // The config the DTB-2 endpoint emits for "a number line where students mark
  // one half": axis [0,1], snap 0.5, so ½ is the single exact tick to the right
  // of the origin. (We use halves, not quarters, so the reported value is exact:
  // the number-line's snap rounds step 0.25 to one decimal, which would report
  // 0.8 for ¾ — a separate widget quirk we don't want to bake into a demo
  // assertion.)
  const NUMBER_LINE_CONFIG = '{ "min": 0, "max": 1, "step": 0.5, "label": "Mark 1/2 on the number line" }';

  test('a student marks the AI-described number line and the reported answer is 0.5', async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(err.message));

    // The playground is public and backend-free; ?kind selects the widget the
    // AI proposed for the demo prompt.
    const response = await page.goto('/widgets/dev?kind=number-line');
    expect(response?.ok(), 'GET /widgets/dev should return 2xx').toBeTruthy();

    // Drop in the exact config the AI emits for the demo sentence. The preview
    // remounts on config change (InteractiveWidget is keyed on the config text).
    const configField = page.getByLabel('Config JSON');
    await configField.fill(NUMBER_LINE_CONFIG);

    // The widget renders inside the sandboxed iframe (sandbox="allow-scripts",
    // deliberately no allow-same-origin). Playwright drives it at the browser
    // protocol level, so it can interact across the sandbox boundary that
    // scripts cannot cross.
    const widgetFrame = page.frameLocator('iframe[title="Interactive question widget"]');
    const slider = widgetFrame.getByRole('slider');
    await expect(slider, 'the AI-described number line should render in the sandbox').toBeVisible();

    // Before any interaction the widget reports nothing — the answer field
    // stays blank so a student can leave a question unanswered (no
    // reportValue-on-mount). The host panel proves that.
    await expect(page.getByText('No value reported yet.')).toBeVisible();

    // Student interaction. Click focuses the slider and reports the value under
    // the pointer; we then anchor deterministically with Home (→ min, 0) and
    // step once to the right with ArrowRight (→ +step, 0.5 = ½), independent of
    // where the click happened to land.
    await slider.click();
    await slider.press('Home');
    await slider.press('ArrowRight');

    // The grade signal: the host received 0.5 across the postMessage boundary —
    // this is the value the deterministic per-subpart grader would score against
    // `correct_answer`. AI authored the widget; it never touched this number.
    await expect(
      page.locator('pre'),
      'host should receive the student answer 0.5',
    ).toHaveText('0.5');

    // Capture the demo screenshot reproducibly into the golden-path asset dir.
    await page.screenshot({
      path: 'e2e/__artifacts__/dtb4-describe-to-build.png',
      fullPage: true,
    });

    // The whole runtime path must be clean — a console error here usually means
    // the sandbox bridge or a widget threw.
    expect(
      consoleErrors,
      `console errors during the runtime smoke:\n${consoleErrors.join('\n')}`,
    ).toEqual([]);
  });
});
