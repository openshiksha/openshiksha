/**
 * Widget runtime — the code that runs **inside** the sandboxed iframe.
 *
 * This module exports `buildRuntimeBoot(...)` which returns the
 * self-contained `<script>` body the host bakes into the srcdoc. The
 * function is built as a string because:
 *
 *   - The iframe runs at an **opaque origin** and has no access to the app
 *     bundle — anything it executes must be inline in its srcdoc.
 *   - The host module (`host.ts`) already builds the rest of the srcdoc;
 *     this file just owns the *runtime body* that wraps a widget's
 *     `renderSource` with SDK hooks (`reportValue`, `requestResize`,
 *     auto-`resize` via `ResizeObserver`, error trapping).
 *
 * Contract with `defineWidget`:
 *
 *   - The widget's `renderSource` is a single function expression whose
 *     parameter is `ctx`. The runtime injects it as
 *     `var __widgetRender = (RENDERSOURCE);` and then calls
 *     `__widgetRender(ctx)`.
 *   - `ctx.reportValue(v)` posts a typed `value` message; `ctx.requestResize()`
 *     forces an immediate `resize` post.
 *   - Any exception thrown synchronously by `render` becomes a typed
 *     `error` message; the host renders a branded error state.
 */

import { WIDGET_PROTOCOL_VERSION } from './protocol';

/**
 * Build the runtime `<script>` that boots a widget inside the sandbox.
 *
 * Inputs are *all* serialised into the script — there is no shared scope
 * between host and runtime by design. The init payload is already JSON
 * (built by `host.ts`); this function only needs to know which widget's
 * `renderSource` to wrap.
 *
 * Returned value is the *entire* `<script>...</script>` tag, ready to be
 * concatenated into the srcdoc body.
 */
export function buildRuntimeBoot(params: {
  /** JSON-encoded `InitMessage` payload to bake into the boot. */
  initJson: string;
  /** Widget kind for diagnostics + error messages. */
  kind: string;
  /** Stringified body of the widget's `render` function (from `WidgetModule.renderSource`). */
  renderSource: string;
}): string {
  // Escape '<' so an authored `</script>` inside `renderSource` or the init
  // payload cannot terminate the inline boot script. The IW-1a/b XSS-defence
  // already covers config payloads coming from the DB; this is the same
  // defence applied to the runtime body.
  const safeInit = params.initJson.replace(/</g, '\\u003c');
  const safeRender = params.renderSource.replace(/<\/script>/gi, '<\\u002fscript>');
  const safeKind = JSON.stringify(params.kind);

  return `<script>
(function () {
  var PROTOCOL = ${WIDGET_PROTOCOL_VERSION};
  var KIND = ${safeKind};
  var initPayload = ${safeInit};

  function post(msg) {
    try { parent.postMessage(msg, '*'); } catch (e) {}
  }
  function emitResize() {
    var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    post({ type: 'resize', protocol: PROTOCOL, height: h });
  }
  function emitError(message) {
    post({ type: 'error', protocol: PROTOCOL, message: String(message).slice(0, 240) });
  }

  // Announce we're alive. The host pairs ready ↔ init in IW-2+ (when init
  // arrives over postMessage rather than being baked); for IW-1c the
  // payload is already inline and we render synchronously.
  post({ type: 'ready', protocol: PROTOCOL });

  function boot() {
    var mount = document.getElementById('widget-root');
    if (!mount) {
      emitError('runtime: #widget-root missing');
      return;
    }
    var ctx = {
      mount: mount,
      config: initPayload.config || {},
      variables: initPayload.variables || {},
      imageBase: initPayload.imageBase || '',
      reportValue: function (v) {
        post({ type: 'value', protocol: PROTOCOL, value: v });
      },
      reportStep: function (s) {
        // Defensive: only forward a well-formed step. The verdict must be one of
        // the three known states; anything else is dropped rather than escaping
        // the sandbox malformed (the host also type-guards on receipt).
        if (!s || typeof s !== 'object') return;
        var verdict = s.verdict;
        if (verdict !== 'ok' && verdict !== 'bad' && verdict !== 'neutral') return;
        post({
          type: 'step',
          protocol: PROTOCOL,
          previous: String(s.previous == null ? '' : s.previous),
          current: String(s.current == null ? '' : s.current),
          verdict: verdict,
          reason: String(s.reason == null ? '' : s.reason)
        });
      },
      requestResize: function () { emitResize(); },
    };
    try {
      var __widgetRender = (${safeRender});
      __widgetRender(ctx);
    } catch (e) {
      emitError('widget(' + KIND + '): ' + (e && e.message ? e.message : e));
      return;
    }
    // Auto-resize: fire once after render, then on every body-size change.
    emitResize();
    if (typeof ResizeObserver !== 'undefined') {
      try { new ResizeObserver(emitResize).observe(document.body); } catch (e) {}
    }
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    boot();
  } else {
    window.addEventListener('DOMContentLoaded', boot);
  }
})();
</script>`;
}
