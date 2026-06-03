import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { RichContent } from './RichContent';

/**
 * Renders an authored interactive question widget (M7-11) inside a **sandboxed
 * iframe** so its embedded `<script>` can run without reaching the host app.
 *
 * SECURITY — the iframe uses `sandbox="allow-scripts"` and deliberately NOT
 * `allow-same-origin`. The combination of those two would let the untrusted
 * authored script read the app's cookies/storage/DOM and defeats the whole
 * point; never add `allow-same-origin` here. The widget HTML is delivered only
 * via `srcDoc` (an opaque-origin document) — it is never injected into the app
 * DOM (no `dangerouslySetInnerHTML` of the raw widget).
 *
 * Token resolution already happened server-side: image `#{...}#` tokens were
 * resolved to absolute URLs at import, and `{{var}}` values were substituted
 * per student by the API serializer. This component only wraps + sandboxes.
 */
export interface InteractiveWidgetProps {
  /** Resolved widget HTML (script + markup) from `subpart.interactive_html`. */
  html: string;
  /** Script-free fallback rendered if there is no widget HTML. */
  fallbackText?: string;
  /** Min iframe height before the widget reports its own (px). */
  minHeight?: number;
  className?: string;
}

// Pinned 2015-era libraries the legacy Cabinet widgets depend on: jQuery +
// jQuery-UI (slider) + jQuery-UI CSS, plus Bootstrap 3 glyphicons for the
// slider/handle markup. Versions are pinned for reproducibility.
// Hardening follow-up: add SRI integrity hashes (the sandbox without
// allow-same-origin is the primary trust boundary).
const VENDOR_HEAD = [
  '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/themes/base/jquery-ui.min.css">',
  '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/3.4.1/css/bootstrap.min.css">',
  '<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>',
  '<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.13.2/jquery-ui.min.js"></script>',
].join('\n');

// Posts the rendered content height to the parent so the iframe can be sized.
// (iframes don't auto-size to srcdoc content.)
const RESIZE_SCRIPT = `<script>
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

function buildSrcDoc(html: string): string {
  return [
    '<!doctype html><html><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    VENDOR_HEAD,
    '<style>body{font-family:Inter,system-ui,sans-serif;margin:8px;color:#1f2937;}</style>',
    '</head><body>',
    html,
    RESIZE_SCRIPT,
    '</body></html>',
  ].join('\n');
}

const InteractiveWidgetImpl = ({
  html,
  fallbackText,
  minHeight = 640,
  className,
}: InteractiveWidgetProps) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(minHeight);
  const srcDoc = useMemo(() => (html ? buildSrcDoc(html) : ''), [html]);

  useEffect(() => {
    function onMessage(e: MessageEvent) {
      // Only trust messages from *this* iframe's window. The sandboxed frame
      // has an opaque origin (event.origin === 'null'), so identity is checked
      // via the source window reference, not the origin string.
      if (e.source !== iframeRef.current?.contentWindow) return;
      const data = e.data as { type?: string; height?: number } | null;
      if (data && data.type === 'os-widget-height' && typeof data.height === 'number') {
        setHeight(Math.max(minHeight, Math.ceil(data.height) + 16));
      }
    }
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [minHeight]);

  // No widget HTML → fall back to the sanitised prose so the question is still
  // shown (the answer input lives outside this component regardless).
  if (!html) {
    return fallbackText ? <RichContent text={fallbackText} variant="block" className={className} /> : null;
  }

  return (
    <iframe
      ref={iframeRef}
      title="Interactive question widget"
      sandbox="allow-scripts"
      srcDoc={srcDoc}
      className={className}
      style={{ width: '100%', height, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' }}
      loading="lazy"
    />
  );
};

export const InteractiveWidget = memo(InteractiveWidgetImpl);
