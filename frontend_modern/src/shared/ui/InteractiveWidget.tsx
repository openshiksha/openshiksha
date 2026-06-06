import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { buildLegacySrcDoc, createHostBridge } from '../../widgets/_sdk/host';
import { RichContent } from './RichContent';

/**
 * Renders an authored interactive question widget inside a **sandboxed iframe**
 * so its embedded `<script>` can run without reaching the host app.
 *
 * **IW-1b (today):** srcdoc construction + message bridge moved out into the
 * Widgets Framework SDK (`frontend_modern/src/widgets/_sdk/host.ts`). The
 * public `InteractiveWidgetProps` shape stays identical, and the legacy thermo
 * rendering path is byte-equivalent — `buildLegacySrcDoc` is the same string
 * the previous inline implementation produced. The bridge now also accepts
 * typed `ready / resize / value / error` messages from the new framework
 * runtime (IW-1c lands the runtime; this component will pick up the
 * kind-based path in a follow-up PR alongside `widget_kind` plumbing).
 *
 * SECURITY — the iframe uses `sandbox="allow-scripts"` and deliberately NOT
 * `allow-same-origin`. The combination of those two would let the untrusted
 * authored script read the app's cookies/storage/DOM and defeats the whole
 * point; never add `allow-same-origin` here. The widget HTML is delivered only
 * via `srcDoc` (an opaque-origin document) — it is never injected into the app
 * DOM (no `dangerouslySetInnerHTML` of the raw widget). Identity of messages
 * coming back from the iframe is enforced via `event.source` (not
 * `event.origin`, which is the literal string `"null"` for an opaque-origin
 * sandboxed document) — `createHostBridge` does that check before our
 * handlers fire.
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

const InteractiveWidgetImpl = ({
  html,
  fallbackText,
  minHeight = 640,
  className,
}: InteractiveWidgetProps) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(minHeight);
  const srcDoc = useMemo(() => (html ? buildLegacySrcDoc(html) : ''), [html]);

  useEffect(() => {
    // The bridge handles both the legacy `'os-widget-height'` message (used by
    // the M7-11 widget today) and the framework's typed `resize` message
    // (used by widgets rendered through the IW-1c runtime). Either way the
    // iframe shrinks/grows to fit content, clamped to `minHeight`.
    const grow = (h: number) => setHeight(Math.max(minHeight, Math.ceil(h) + 16));
    return createHostBridge(() => iframeRef.current, {
      onLegacyHeight: grow,
      onResize: (msg) => grow(msg.height),
    });
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
