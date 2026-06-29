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

import { getWidgetModule } from '../registry';
import {
  isErrorMessage,
  isReadyMessage,
  isResizeMessage,
  isStepMessage,
  isValueMessage,
  WIDGET_PROTOCOL_VERSION,
  type ErrorMessage,
  type InitMessage,
  type ReadyMessage,
  type ResizeMessage,
  type StepMessage,
  type ValueMessage,
  type WidgetMessage,
} from './protocol';
import { buildRuntimeBoot } from './runtime';

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
 * Looks `kind` up in the SDK registry. If the kind is known, the widget's
 * `renderSource` is wrapped by the runtime boot (`buildRuntimeBoot`) and
 * baked into the srcdoc — that's the IW-1c "real" path. If the kind is
 * unknown (typo, version skew, etc.) the srcdoc falls back to a small stub
 * that emits a typed `error` so the host's error UI can render — the
 * framework never silently no-ops.
 */
export function buildHostSrcDoc(params: {
  kind: string;
  config: Record<string, unknown>;
  variables: Record<string, number | string | boolean>;
  imageBase: string;
}): string {
  // The init payload is JSON-serialised once and shared with the runtime
  // boot. Using a `<script>` tag (and NOT `dangerouslySetInnerHTML`) — the
  // only place this string lands is inside `<iframe srcDoc>`, which parses
  // as a standalone document at an opaque origin.
  const initJson = JSON.stringify({
    type: 'init',
    protocol: WIDGET_PROTOCOL_VERSION,
    ...params,
  } satisfies InitMessage);

  // Inline brand tokens so widgets read on-brand from day one (no external
  // stylesheet load — keeps the runtime tiny and cache-warm). Migrating this
  // to a shared `widget-runtime.css` is an IW-1 follow-up if the size grows.
  const inlineStyles = `
    :root {
      --brand-600: #FF6F00;
      --paper: #FBF7EE;
      --ink-900: #1B1A17;
      --ink-300: #BDB6A5;
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

  const widget = getWidgetModule(params.kind);
  const bootScript = widget
    ? buildRuntimeBoot({ initJson, kind: params.kind, renderSource: widget.renderSource })
    : buildUnknownKindBoot(params.kind, initJson);

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

/**
 * Fallback boot used when the requested `kind` is not in the registry. Posts
 * `ready` so the host bridge fires its onReady handler, then emits a typed
 * `error`. The host renders a branded error state; the widget area never
 * silently goes blank.
 */
function buildUnknownKindBoot(kind: string, initJson: string): string {
  const safeKind = JSON.stringify(kind);
  const safeInit = initJson.replace(/</g, '\\u003c');
  return `<script>
(function () {
  var PROTOCOL = ${WIDGET_PROTOCOL_VERSION};
  function post(m) { try { parent.postMessage(m, '*'); } catch (e) {} }
  // Reference the init payload so static analysis sees it was used, even
  // though the unknown-kind branch has nothing to render with it.
  var _init = ${safeInit};
  void _init;
  post({ type: 'ready', protocol: PROTOCOL });
  post({
    type: 'error',
    protocol: PROTOCOL,
    message: 'Unknown widget kind: ' + ${safeKind}
  });
  var note = document.createElement('p');
  note.textContent = 'Unknown widget kind: ' + ${safeKind};
  note.style.color = '#9B1C1C';
  document.body.appendChild(note);
  var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  post({ type: 'resize', protocol: PROTOCOL, height: h });
})();
</script>`;
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
  /** A step-validating widget committed a line (GSV-4b); carries the deterministic verdict. */
  onStep?: (msg: StepMessage) => void;
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
    if (isStepMessage(data)) {
      handlers.onStep?.(data);
      handlers.onWidgetMessage?.(data);
      return;
    }
    // Anything else is silently dropped — never throw on noisy postMessage.
  }

  window.addEventListener('message', onMessage);
  return () => window.removeEventListener('message', onMessage);
}
