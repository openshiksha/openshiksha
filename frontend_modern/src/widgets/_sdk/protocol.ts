/**
 * Interactive Widgets Framework — host ↔ runtime postMessage protocol (IW-1a).
 *
 * This file defines the **only** wire format the sandboxed widget iframe and
 * the parent host are allowed to exchange. Both sides import these types so a
 * widget that violates the contract fails type-check at the SDK boundary, not
 * silently at runtime.
 *
 * Security model — this is plumbing only, but the shape matters:
 *
 *   - The iframe is `sandbox="allow-scripts"` **without** `allow-same-origin`.
 *     Its origin is the opaque `"null"`, so the host *cannot* trust
 *     `event.origin` to identify the widget; it must compare
 *     `event.source === iframe.contentWindow` instead. The bridge in
 *     `host.ts` enforces that — protocol-level types only describe the
 *     payloads themselves.
 *   - Every message carries the protocol version. A widget written against
 *     v1 will refuse to talk to a v2 host (and vice-versa) rather than
 *     silently misbehaving.
 *
 * The wire is intentionally tiny — six message kinds — because adding a kind
 * is a versioned API change. Convenience hooks (`useVariables`,
 * `reportValue`, `requestResize`, `reportStep`) live in the runtime and
 * *compose* these messages; they are not part of the protocol surface.
 *
 * Adding `step` (GSV-4b) is **additive, not breaking**: it is a new
 * widget→host kind that hosts written against the prior surface simply ignore
 * (the bridge silently drops unrecognised messages), so the protocol version
 * stays `1`. It carries only the **deterministic** in-sandbox verdict for a
 * line pair — never anything AI-derived — so the host can route a wrong step
 * to the (host-side, principle-1) AI coach without the sandbox ever touching
 * the network or the AI itself.
 */

/**
 * Increment when **any** breaking change to the message shapes ships.
 * Both sides assert equality at handshake — mismatched versions are treated
 * as an error, not a soft warning.
 */
export const WIDGET_PROTOCOL_VERSION = 1 as const;
export type WidgetProtocolVersion = typeof WIDGET_PROTOCOL_VERSION;

/**
 * Host → widget. Sent exactly once, immediately after the runtime posts
 * `ready`. Carries the kind, the per-student-substituted config, and any
 * sampled variable values the widget may want to display or animate.
 *
 * `imageBase` is the absolute URL prefix to resolve relative asset paths
 * against — widgets should never hard-code app origins.
 */
export interface InitMessage {
  type: 'init';
  protocol: WidgetProtocolVersion;
  kind: string;
  /** Already-resolved per-student config (tokens substituted server-side). */
  config: Record<string, unknown>;
  /** Sampled variable values for the student. May be empty. */
  variables: Record<string, number | string | boolean>;
  /** Absolute URL prefix for resolving relative asset paths. */
  imageBase: string;
}

/**
 * Widget → host. The runtime posts this as soon as the boot script has wired
 * up its listeners. The host responds with `init`. Until the host sees
 * `ready`, it must buffer or drop config — never assume the widget heard it.
 */
export interface ReadyMessage {
  type: 'ready';
  protocol: WidgetProtocolVersion;
}

/**
 * Widget → host. The runtime emits this whenever its content size changes
 * (driven by a `ResizeObserver` inside the runtime). The host clamps to a
 * `minHeight` and resizes the iframe accordingly.
 */
export interface ResizeMessage {
  type: 'resize';
  protocol: WidgetProtocolVersion;
  /** Content height in CSS pixels. The host adds its own padding. */
  height: number;
}

/**
 * Widget → host. Answer-producing widgets call `reportValue(v)` from the SDK;
 * the runtime serialises that to this message. Explanatory widgets (e.g. the
 * legacy thermo sim) never emit one.
 *
 * `value` is `unknown` at the protocol layer — the host is responsible for
 * shape-checking against the subpart's expected answer type before binding it
 * to the answer form. The widget's own JSON Schema describes the value shape
 * for type-checked SDK code at the contributor boundary.
 */
export interface ValueMessage {
  type: 'value';
  protocol: WidgetProtocolVersion;
  value: unknown;
}

/**
 * Widget → host. The runtime catches exceptions thrown by the widget's
 * `render` function (or thrown asynchronously during boot) and re-emits them
 * as `error`. The host renders a branded error state and never lets the
 * widget's stack reach the app surface.
 */
export interface ErrorMessage {
  type: 'error';
  protocol: WidgetProtocolVersion;
  /** Short human-readable summary; never include a stack. */
  message: string;
}

/**
 * Widget → host. Emitted by a step-validating widget (`step-solver`) when a
 * student **commits** a line (on Enter / blur), carrying the *deterministic,
 * in-sandbox* equivalence verdict for that line against the line above it.
 *
 * This message is **never AI** — the verdict comes from the same numeric-probing
 * engine that drives the live ✓/✗ in the sandbox. The host uses it only to feed
 * a *wrong* step (`verdict === 'bad'`) to the host-side AI coach (GSV-3/GSV-4a),
 * which re-checks correctness server-side before ever consulting the LLM. So the
 * sandbox stays network-less and AI-free (principle 1) and AI stays out of the
 * grade path (principle 2) — `step` is a coaching signal, not a grade.
 *
 * `verdict` mirrors the widget's on-screen marker state: `'ok'` (✓ equivalent),
 * `'bad'` (✗ changes the answer), `'neutral'` (couldn't parse this line yet —
 * the deterministic fallback). The host treats only `'bad'` as coachable.
 */
export interface StepMessage {
  type: 'step';
  protocol: WidgetProtocolVersion;
  /** The committed line directly above (the student's prior line, or the prompt). */
  previous: string;
  /** The line the student just committed. */
  current: string;
  /** Deterministic in-sandbox verdict for `current` vs `previous`. */
  verdict: 'ok' | 'bad' | 'neutral';
  /** The engine's short deterministic reason for the verdict. */
  reason: string;
}

/** Union of every message the host ever sends. */
export type HostMessage = InitMessage;

/** Union of every message the widget runtime ever sends. */
export type WidgetMessage = ReadyMessage | ResizeMessage | ValueMessage | ErrorMessage | StepMessage;

// ── Type guards ───────────────────────────────────────────────────────────
//
// Type guards live with the types so consumers don't roll their own. They
// only check the *discriminant* and the protocol version; payload shape is
// the wire contract above and is responsibility of the sender.

function isWidgetEnvelope(data: unknown): data is { type: string; protocol: number } {
  if (typeof data !== 'object' || data === null) return false;
  const d = data as { type?: unknown; protocol?: unknown };
  return typeof d.type === 'string' && d.protocol === WIDGET_PROTOCOL_VERSION;
}

export function isInitMessage(data: unknown): data is InitMessage {
  return isWidgetEnvelope(data) && data.type === 'init';
}

export function isReadyMessage(data: unknown): data is ReadyMessage {
  return isWidgetEnvelope(data) && data.type === 'ready';
}

export function isResizeMessage(data: unknown): data is ResizeMessage {
  return (
    isWidgetEnvelope(data) &&
    data.type === 'resize' &&
    typeof (data as ResizeMessage).height === 'number'
  );
}

export function isValueMessage(data: unknown): data is ValueMessage {
  return isWidgetEnvelope(data) && data.type === 'value';
}

export function isErrorMessage(data: unknown): data is ErrorMessage {
  return (
    isWidgetEnvelope(data) &&
    data.type === 'error' &&
    typeof (data as ErrorMessage).message === 'string'
  );
}

export function isStepMessage(data: unknown): data is StepMessage {
  if (!isWidgetEnvelope(data) || data.type !== 'step') return false;
  const d = data as Partial<StepMessage>;
  return (
    typeof d.previous === 'string' &&
    typeof d.current === 'string' &&
    typeof d.reason === 'string' &&
    (d.verdict === 'ok' || d.verdict === 'bad' || d.verdict === 'neutral')
  );
}

export function isWidgetMessage(data: unknown): data is WidgetMessage {
  return (
    isReadyMessage(data) ||
    isResizeMessage(data) ||
    isValueMessage(data) ||
    isErrorMessage(data) ||
    isStepMessage(data)
  );
}
