/**
 * Interactive Widgets Framework — host module (IW-1b).
 *
 * This file owns two things and only two things:
 *
 *   1. **srcdoc construction.** Build the document that goes into the
 *      sandboxed `<iframe srcDoc=...>` for both paths:
 *        - `buildLegacySrcDoc(html)` — the M7-11 escape hatch that wraps
 *          authored raw HTML + the jQuery / jQuery-UI / Bootstrap vendor
 *          head. **Byte-equivalent** to the previous inline implementation
 *          in `InteractiveWidget.tsx` so the legacy thermo question keeps
 *          rendering unchanged.
 *        - `buildHostSrcDoc({ kind, config, variables, imageBase })` — the
 *          going-forward Widgets Framework path. Boots a minimal runtime that
 *          looks up `kind` in the SDK registry (lands in IW-1c) and mounts the
 *          widget's React component. **No vendor libs** — React-only.
 *   2. **Message bridge.** `createHostBridge(iframe, handlers)` wires a
 *      `window.addEventListener('message', ...)` that filters every event
 *      through `event.source === iframe.contentWindow` *before* doing
 *      anything else. That source guard is the security boundary — a
 *      `sandbox="allow-scripts"` iframe without `allow-same-origin` has
 *      `event.origin === "null"`, so the origin string cannot be used.
 *
 * **The iframe attributes themselves stay in the React component**
 * (`InteractiveWidget.tsx`) — they're declared on the `<iframe>` element so
 * React's type-system + the existing visual-regression tests catch any
 * regression. The host module never builds an iframe; it only builds *what
 * goes into one*.
 *
 * Anything else (hooks, schema validation, registry lookup) lives in the
 * runtime (`runtime.ts`, IW-1c) or per-widget modules.
 */

import {
  isErrorMessage,
  isReadyMessage,
  isResizeMessage,
  isValueMessage,
  WIDGET_PROTOCOL_VERSION,
  type ErrorMessage,
  type InitMessage,
  type ReadyMessage,
  type ResizeMessage,
  type ValueMessage,
  type WidgetMessage,
} from './protocol';

// ── srcdoc construction ───────────────────────────────────────────────────

// Pinned 2015-era libraries the legacy Cabinet widgets depend on. Versions
// pinned for reproducibility. Hardening follow-up: add SRI integrity hashes.
// The sandbox without `allow-same-origin` is the primary trust boundary.
const LEGACY_VENDOR_HEAD = [
  '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/themes/base/jquery-ui.min.css">',
  '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/3.4.1/css/bootstrap.min.css">',
  '<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>',
  '<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/jquery-ui.min.js"></script>',
].join('\n');

// Legacy resize script — posts the rendered content height as the
// `'os-widget-height'` message the existing host listener understands.
// Kept identical to the M7-11 implementation so the thermo question's
// resize behaviour does not regress with this PR.
const LEGACY_RESIZE_SCRIPT = `<script>
(function () {
  function post() {
    try {
      var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
      parent.postMessage({ type: 'os-widget-height', height: h }, '*');
    } catch (e) {}
  }
  window.addEventListener('load', post);
  setTimeout(post, 300);
  setTimeout(post, 1200);
})();
</script>`;

/**
 * Build the srcdoc for the **legacy / escape-hatch** path (M7-11).
 *
 * The returned string is byte-equivalent to what `InteractiveWidget.tsx`
 * used to produce inline. Moving the implementation here is a pure refactor
 * — the legacy thermo question must keep rendering identically.
 */
export function buildLegacySrcDoc(html: string): string {
  return [
    '<!doctype html><html><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    LEGACY_VENDOR_HEAD,
    '<style>body{font-family:Inter,system-ui,sans-serif;margin:8px;color:#1f2937;}</style>',
    '</head><body>',
    html,
    LEGACY_RESIZE_SCRIPT,
    '</body></html>',
  ].join('\n');
}

/**
 * Build the srcdoc for the **going-forward Widgets Framework** path
 * (kind-based; no vendor libs).
 *
 * For IW-1b this returns a runtime stub that:
 *   - posts a typed `ready` message at load
 *   - listens for the host's `init` and renders a tiny placeholder
 *   - emits typed `resize` messages whenever its content size changes
 *
 * IW-1c replaces the stub body with the real runtime that looks up `kind`
 * in `registry.ts` and mounts the widget's React component. The wire shape
 * the host listens to is finalised here, so IW-1c is a body swap, not an
 * API change.
 */
export function buildHostSrcDoc(params: {
  kind: string;
  config: Record<string, unknown>;
  variables: Record<string, number | string | boolean>;
  imageBase: string;
}): string {
  // The init payload is encoded as JSON inside the boot script. Using a
  // `<script>` tag (and NOT `dangerouslySetInnerHTML`) — the only place this
  // string ever lands is inside an `<iframe srcDoc>`, which is parsed as a
  // standalone document at an opaque origin.
  const initJson = JSON.stringify({
    type: 'init',
    protocol: WIDGET_PROTOCOL_VERSION,
    ...params,
  } satisfies InitMessage);
  const escapedInit = initJson.replace(/</g, '\\u003c');

  // Inline brand tokens so widgets read on-brand from day one (no external
  // stylesheet load — keeps the runtime tiny and cache-warm). IW-1c will move
  // this into a shared widget-runtime.css if the size grows.
  const inlineStyles = `
    :root {
      --brand-600: #FF6F00;
      --paper: #FBF7EE;
      --ink-900: #1B1A17;
    }
    html, body {
      margin: 0;
      padding: 12px;
      font-family: Inter, system-ui, -apple-system, sans-serif;
      color: var(--ink-900);
      background: var(--paper);
    }
    h1, h2, h3 { font-family: "Fraunces", Georgia, serif; }
  `;

  const bootScript = `<script>
(function () {
  var PROTOCOL = ${WIDGET_PROTOCOL_VERSION};
  var initPayload = ${escapedInit};

  function post(msg) {
    try { parent.postMessage(msg, '*'); } catch (e) {}
  }

  function emitResize() {
    var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    post({ type: 'resize', protocol: PROTOCOL, height: h });
  }

  // Tell the host we're alive. The host replies with init; for the IW-1b
  // stub we already have the payload baked in, so we just render directly.
  post({ type: 'ready', protocol: PROTOCOL });

  function renderStub() {
    var root = document.getElementById('widget-root');
    if (!root) return;
    root.innerHTML = '';
    var note = document.createElement('p');
    note.textContent = 'Widget runtime stub · kind = ' + String(initPayload.kind);
    root.appendChild(note);
    emitResize();
  }

  if (typeof ResizeObserver !== 'undefined') {
    try { new ResizeObserver(emitResize).observe(document.body); } catch (e) {}
  }
  window.addEventListener('load', renderStub);
  // Belt-and-braces in case 'load' already fired by the time we got here.
  if (document.readyState === 'complete') renderStub();
})();
</script>`;

  return [
    '<!doctype html><html><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<style>${inlineStyles}</style>`,
    '</head><body>',
    '<div id="widget-root"></div>',
    bootScript,
    '</body></html>',
  ].join('\n');
}

// ── Message bridge ────────────────────────────────────────────────────────

/**
 * Handlers a consumer can register on the host bridge. All optional — a
 * legacy-path host only needs `onLegacyHeight`; a framework-path host adds
 * `onReady` / `onResize` / `onValue` / `onError`.
 *
 * Handlers fire *only* when `event.source === iframe.contentWindow` —
 * messages from other windows or extensions are ignored before reaching the
 * caller. This is the security guarantee `createHostBridge` exists to make.
 */
export interface HostBridgeHandlers {
  /** Legacy resize message: `{ type: 'os-widget-height', height }`. */
  onLegacyHeight?: (height: number) => void;
  onReady?: (msg: ReadyMessage) => void;
  onResize?: (msg: ResizeMessage) => void;
  onValue?: (msg: ValueMessage) => void;
  onError?: (msg: ErrorMessage) => void;
  /** Catch-all for any well-typed widget message; runs after the per-type handler. */
  onWidgetMessage?: (msg: WidgetMessage) => void;
}

/**
 * Wire a `message` listener that only fires for the bound iframe. Returns a
 * cleanup function that removes the listener — call it in your React effect's
 * cleanup branch.
 *
 * The bridge accepts both the **typed protocol** (`ready` / `resize` /
 * `value` / `error`) and the **legacy** `'os-widget-height'` shape, so an
 * `InteractiveWidget` that still uses the legacy srcdoc continues to resize
 * correctly through this same call.
 */
export function createHostBridge(
  getIframe: () => HTMLIFrameElement | null,
  handlers: HostBridgeHandlers,
): () => void {
  function onMessage(event: MessageEvent) {
    const iframe = getIframe();
    // Identity guard — see file header. An `allow-scripts` sandbox has an
    // opaque origin (`event.origin === "null"`), so the only trustworthy
    // identifier is the source window reference. Anything else is rejected.
    if (!iframe || event.source !== iframe.contentWindow) return;

    const data = event.data as unknown;

    // Legacy `'os-widget-height'` path. Kept here so the M7-11 widget
    // continues to size correctly without reaching for the typed bridge.
    if (
      typeof data === 'object' &&
      data !== null &&
      (data as { type?: unknown }).type === 'os-widget-height' &&
      typeof (data as { height?: unknown }).height === 'number'
    ) {
      handlers.onLegacyHeight?.((data as { height: number }).height);
      return;
    }

    // Typed protocol path.
    if (isReadyMessage(data)) {
      handlers.onReady?.(data);
      handlers.onWidgetMessage?.(data);
      return;
    }
    if (isResizeMessage(data)) {
      handlers.onResize?.(data);
      handlers.onWidgetMessage?.(data);
      return;
    }
    if (isValueMessage(data)) {
      handlers.onValue?.(data);
      handlers.onWidgetMessage?.(data);
      return;
    }
    if (isErrorMessage(data)) {
      handlers.onError?.(data);
      handlers.onWidgetMessage?.(data);
      return;
    }
    // Anything else is silently dropped — never throw on noisy postMessage.
  }

  window.addEventListener('message', onMessage);
  return () => window.removeEventListener('message', onMessage);
}
