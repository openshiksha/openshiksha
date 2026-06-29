/**
 * Tests for the Widgets Framework host module (IW-1b).
 *
 * Coverage targets the DoD from the plan:
 *
 *   1. `buildLegacySrcDoc(html)` — sandbox-friendly (NO `allow-same-origin`
 *      ever referenced), preserves the legacy vendor head + resize script,
 *      and is byte-equivalent to what `InteractiveWidget.tsx` used to inline.
 *   2. `buildHostSrcDoc(...)` — framework path; ships the typed protocol's
 *      `ready` + `resize` wiring; bakes the init payload in safely (no
 *      raw `<` that could break out of the script tag).
 *   3. `createHostBridge(...)` — ignores messages whose `event.source` is
 *      not the bound iframe; correctly dispatches both the legacy
 *      `os-widget-height` shape and the typed protocol messages.
 */

import { describe, expect, it, vi } from 'vitest';
import { buildHostSrcDoc, buildLegacySrcDoc, createHostBridge } from './host';
import { WIDGET_PROTOCOL_VERSION } from './protocol';

describe('buildLegacySrcDoc', () => {
  it('never references allow-same-origin (the iframe attr is set on the element, but the srcdoc itself must not opt in)', () => {
    const srcDoc = buildLegacySrcDoc('<p>x</p>');
    expect(srcDoc).not.toContain('allow-same-origin');
  });

  it('keeps the M7-11 vendor head so the legacy thermo widget renders identically', () => {
    const srcDoc = buildLegacySrcDoc('<p>x</p>');
    expect(srcDoc).toContain('jquery/3.6.0/jquery.min.js');
    expect(srcDoc).toContain('jqueryui/1.13.2/jquery-ui.min.js');
    expect(srcDoc).toContain('bootstrap/3.4.1/css/bootstrap.min.css');
  });

  it('keeps the legacy os-widget-height postMessage shape (consumed by the InteractiveWidget bridge)', () => {
    const srcDoc = buildLegacySrcDoc('<p>x</p>');
    expect(srcDoc).toContain("type: 'os-widget-height'");
  });

  it('embeds the authored HTML verbatim inside the body', () => {
    const html = '<canvas id="piston"></canvas><script>var x=42;</script>';
    const srcDoc = buildLegacySrcDoc(html);
    expect(srcDoc).toContain(html);
  });
});

describe('buildHostSrcDoc', () => {
  const baseParams = {
    kind: 'thermo-piston',
    config: { initialVolume: 5 },
    variables: { a: 5 },
    imageBase: 'https://example.com/',
  };

  it('declares no vendor libs — the framework runtime is React-only', () => {
    const srcDoc = buildHostSrcDoc(baseParams);
    expect(srcDoc).not.toContain('jquery');
    expect(srcDoc).not.toContain('bootstrap');
  });

  it('bakes the init payload with the current protocol version', () => {
    const srcDoc = buildHostSrcDoc(baseParams);
    expect(srcDoc).toContain(`"protocol":${WIDGET_PROTOCOL_VERSION}`);
    expect(srcDoc).toContain('"kind":"thermo-piston"');
    expect(srcDoc).toContain('"initialVolume":5');
  });

  it('escapes embedded `<` in the init payload so it cannot break out of the boot script', () => {
    const srcDoc = buildHostSrcDoc({
      ...baseParams,
      config: { evil: '</script><script>alert(1)</script>' },
    });
    // The raw closing tag must not appear inside the inline boot script (it
    // would terminate it). The escape rewrites every '<' to '<'; `>` is
    // harmless in a script context so it is left as-is.
    expect(srcDoc).not.toContain('</script><script>alert(1)');
    expect(srcDoc).toContain('\\u003c/script>\\u003cscript>alert(1)\\u003c/script>');
  });

  it('posts typed ready + resize messages (the wire IW-1c will use)', () => {
    const srcDoc = buildHostSrcDoc(baseParams);
    expect(srcDoc).toContain("type: 'ready'");
    expect(srcDoc).toContain("type: 'resize'");
  });

  it('uses brand tokens inside the sandbox so the runtime feels on-brand', () => {
    const srcDoc = buildHostSrcDoc(baseParams);
    expect(srcDoc).toContain('#FF6F00');
    expect(srcDoc).toContain('Fraunces');
  });

  // IW-1c branch coverage — registry-resolved kind vs. unknown kind.
  describe('registry resolution', () => {
    it('bakes the widget`s renderSource into the boot when the kind is known', () => {
      const srcDoc = buildHostSrcDoc({
        kind: '_hello',
        config: { kind: '_hello' },
        variables: {},
        imageBase: '',
      });
      // `__widgetRender` is the runtime`s wrapper variable name — its
      // presence means we`re on the registry-resolved path, not the
      // unknown-kind fallback.
      expect(srcDoc).toContain('__widgetRender');
      // The hello widget`s body content (`Widget runtime alive`) must end up
      // inlined into the boot script via toString().
      expect(srcDoc).toContain('Widget runtime alive');
    });

    it('falls back to a typed `error` boot when the kind is unknown', () => {
      const srcDoc = buildHostSrcDoc({
        kind: 'totally-made-up-kind',
        config: {},
        variables: {},
        imageBase: '',
      });
      expect(srcDoc).not.toContain('__widgetRender');
      expect(srcDoc).toContain("type: 'error'");
      expect(srcDoc).toContain('Unknown widget kind');
      expect(srcDoc).toContain('totally-made-up-kind');
    });
  });
});

describe('createHostBridge', () => {
  function postFromSource(source: unknown, data: unknown) {
    // Construct a real MessageEvent so the bridge sees `event.source` exactly
    // as the browser would deliver it. `dispatchEvent` makes the listener fire
    // synchronously.
    const event = new MessageEvent('message', { data, source: source as Window });
    window.dispatchEvent(event);
  }

  it('ignores messages whose source is not the bound iframe', () => {
    const fakeIframe = { contentWindow: {} } as unknown as HTMLIFrameElement;
    const onLegacyHeight = vi.fn();
    const onResize = vi.fn();
    const cleanup = createHostBridge(() => fakeIframe, { onLegacyHeight, onResize });

    // A message from some *other* window — e.g. a browser extension or a
    // different iframe — must not trigger any handler.
    postFromSource(window, { type: 'os-widget-height', height: 999 });
    postFromSource({}, {
      type: 'resize',
      protocol: WIDGET_PROTOCOL_VERSION,
      height: 999,
    });

    expect(onLegacyHeight).not.toHaveBeenCalled();
    expect(onResize).not.toHaveBeenCalled();
    cleanup();
  });

  it('delivers legacy os-widget-height messages from the bound iframe', () => {
    const sourceWin = {} as Window;
    const iframe = { contentWindow: sourceWin } as unknown as HTMLIFrameElement;
    const onLegacyHeight = vi.fn();
    const cleanup = createHostBridge(() => iframe, { onLegacyHeight });

    postFromSource(sourceWin, { type: 'os-widget-height', height: 240 });
    expect(onLegacyHeight).toHaveBeenCalledWith(240);
    cleanup();
  });

  it('delivers typed protocol messages from the bound iframe', () => {
    const sourceWin = {} as Window;
    const iframe = { contentWindow: sourceWin } as unknown as HTMLIFrameElement;
    const onReady = vi.fn();
    const onResize = vi.fn();
    const onValue = vi.fn();
    const onError = vi.fn();
    const onStep = vi.fn();
    const onWidgetMessage = vi.fn();
    const cleanup = createHostBridge(() => iframe, {
      onReady,
      onResize,
      onValue,
      onError,
      onStep,
      onWidgetMessage,
    });

    postFromSource(sourceWin, { type: 'ready', protocol: WIDGET_PROTOCOL_VERSION });
    postFromSource(sourceWin, { type: 'resize', protocol: WIDGET_PROTOCOL_VERSION, height: 120 });
    postFromSource(sourceWin, { type: 'value', protocol: WIDGET_PROTOCOL_VERSION, value: 42 });
    postFromSource(sourceWin, {
      type: 'error',
      protocol: WIDGET_PROTOCOL_VERSION,
      message: 'boom',
    });
    postFromSource(sourceWin, {
      type: 'step',
      protocol: WIDGET_PROTOCOL_VERSION,
      previous: '2x + 3 = 7',
      current: '2x = 10',
      verdict: 'bad',
      reason: 'This changes the solution.',
    });

    expect(onReady).toHaveBeenCalledTimes(1);
    expect(onResize).toHaveBeenCalledWith(expect.objectContaining({ height: 120 }));
    expect(onValue).toHaveBeenCalledWith(expect.objectContaining({ value: 42 }));
    expect(onError).toHaveBeenCalledWith(expect.objectContaining({ message: 'boom' }));
    expect(onStep).toHaveBeenCalledWith(
      expect.objectContaining({ current: '2x = 10', verdict: 'bad' }),
    );
    expect(onWidgetMessage).toHaveBeenCalledTimes(5);
    cleanup();
  });

  it('drops malformed messages instead of throwing', () => {
    const sourceWin = {} as Window;
    const iframe = { contentWindow: sourceWin } as unknown as HTMLIFrameElement;
    const onWidgetMessage = vi.fn();
    const cleanup = createHostBridge(() => iframe, { onWidgetMessage });

    expect(() => postFromSource(sourceWin, null)).not.toThrow();
    expect(() => postFromSource(sourceWin, 'string')).not.toThrow();
    expect(() => postFromSource(sourceWin, { type: 'unknown' })).not.toThrow();
    expect(onWidgetMessage).not.toHaveBeenCalled();
    cleanup();
  });

  it('cleanup detaches the listener', () => {
    const sourceWin = {} as Window;
    const iframe = { contentWindow: sourceWin } as unknown as HTMLIFrameElement;
    const onLegacyHeight = vi.fn();
    const cleanup = createHostBridge(() => iframe, { onLegacyHeight });
    cleanup();
    postFromSource(sourceWin, { type: 'os-widget-height', height: 100 });
    expect(onLegacyHeight).not.toHaveBeenCalled();
  });
});
