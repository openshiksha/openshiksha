import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { buildHostSrcDoc, buildLegacySrcDoc, createHostBridge } from '../../widgets/_sdk/host';
import { RichContent } from './RichContent';

/**
 * Renders an authored interactive question widget inside a **sandboxed iframe**
 * so its embedded `<script>` can run without reaching the host app.
 *
 * Two modes (the prop you pass picks the path):
 *
 *   - **`kind` / `config`** (the going-forward Widgets Framework path,
 *     IW-1c+). The kind is looked up in `widgets/registry.ts`; the widget's
 *     render function is serialised + wrapped by the runtime boot
 *     (`buildHostSrcDoc` → `buildRuntimeBoot`) and inlined into the srcdoc.
 *     Unknown kinds render a branded "unknown widget kind" message and emit
 *     a typed `error`.
 *   - **`html`** (the legacy / escape-hatch path, M7-11). The authored HTML
 *     (including its `<script>`) is wrapped with the legacy vendor head
 *     (`buildLegacySrcDoc`). Byte-equivalent to the pre-IW-1b implementation
 *     so the thermo question keeps rendering. IW-7 deprecates this prop.
 *
 * SECURITY — the iframe uses `sandbox="allow-scripts"` and deliberately NOT
 * `allow-same-origin`. The combination of those two would let the untrusted
 * authored script read the app's cookies/storage/DOM and defeats the whole
 * point; never add `allow-same-origin` here. The widget HTML is delivered
 * only via `srcDoc` (an opaque-origin document) — it is never injected into
 * the app DOM (no `dangerouslySetInnerHTML` of the raw widget). Identity of
 * messages coming back from the iframe is enforced via `event.source` (not
 * `event.origin`, which is the literal string `"null"` for an opaque-origin
 * sandboxed document) — `createHostBridge` does that check before our
 * handlers fire.
 *
 * Token resolution already happened server-side: image `#{...}#` tokens were
 * resolved to absolute URLs at import, and `{{var}}` values were substituted
 * per student by the API serializer (`question_text`, `options`,
 * `interactive_html`, and `widget_config` — IW-3b). This component only
 * wraps + sandboxes.
 */
export interface InteractiveWidgetProps {
  /** Framework path — registry kind to look up. Mutually exclusive with `html`. */
  kind?: string;
  /** Already-resolved per-student widget config. Required when `kind` is set. */
  config?: Record<string, unknown>;
  /** Sampled variable values for the student. */
  variables?: Record<string, number | string | boolean>;
  /** Absolute URL prefix for relative asset paths inside the widget. */
  imageBase?: string;
  /** Legacy path — resolved widget HTML from `subpart.interactive_html`. */
  html?: string;
  /** Script-free fallback rendered if there is no widget HTML or kind. */
  fallbackText?: string;
  /** Min iframe height before the widget reports its own (px). */
  minHeight?: number;
  className?: string;
}

const InteractiveWidgetImpl = ({
  kind,
  config,
  variables,
  imageBase,
  html,
  fallbackText,
  minHeight = 640,
  className,
}: InteractiveWidgetProps) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(minHeight);
  // Error state is stored *with* the srcDoc it belongs to. When `srcDoc`
  // changes (new kind / new config), the previously stored error
  // automatically stops being visible without us having to clear it inside
  // the effect — that pattern trips `react-hooks/set-state-in-effect` and
  // the React docs explicitly recommend deriving instead
  // (https://react.dev/learn/you-might-not-need-an-effect).
  const [reportedError, setReportedError] = useState<{ srcDoc: string; message: string } | null>(
    null,
  );

  // `kind` wins when both are present — the framework path is the
  // going-forward contract; `html` is the legacy escape hatch.
  const srcDoc = useMemo(() => {
    if (kind) {
      return buildHostSrcDoc({
        kind,
        config: config ?? {},
        variables: variables ?? {},
        imageBase: imageBase ?? '',
      });
    }
    return html ? buildLegacySrcDoc(html) : '';
  }, [kind, config, variables, imageBase, html]);

  const errorMessage = reportedError && reportedError.srcDoc === srcDoc ? reportedError.message : null;

  useEffect(() => {
    // The reported height already includes the runtime body's own padding
    // (12 px top/bottom), so we only need a small visual buffer here.
    // Adding the previous +16 left a chunk of unused space below the widget.
    const grow = (h: number) => setHeight(Math.max(minHeight, Math.ceil(h) + 4));
    return createHostBridge(() => iframeRef.current, {
      onLegacyHeight: grow,
      onResize: (msg) => grow(msg.height),
      onError: (msg) => setReportedError({ srcDoc, message: msg.message }),
    });
  }, [minHeight, srcDoc]);

  // Neither mode has content → fall back to the sanitised prose so the
  // question is still shown (the answer input lives outside this component).
  if (!srcDoc) {
    return fallbackText ? <RichContent text={fallbackText} variant="block" className={className} /> : null;
  }

  // V2 shell — warm paper card + brand-tinted top border so the runtime
  // reads as part of the product, not a third-party embed. The iframe body
  // already paints its own background; the wrapper just frames it on-brand.
  return (
    <div className={className}>
      <iframe
        ref={iframeRef}
        title="Interactive question widget"
        sandbox="allow-scripts"
        srcDoc={srcDoc}
        style={{
          width: '100%',
          height,
          border: '1px solid #E7E2D3',
          borderTop: '2px solid #FF6F00',
          borderRadius: 10,
          background: '#FBF7EE',
        }}
        loading="lazy"
      />
      {errorMessage && (
        <p style={{ marginTop: 8, color: '#9B1C1C', fontSize: 13 }} role="alert">
          Widget error: {errorMessage}
        </p>
      )}
    </div>
  );
};

export const InteractiveWidget = memo(InteractiveWidgetImpl);
