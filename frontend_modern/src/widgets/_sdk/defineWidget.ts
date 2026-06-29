/**
 * `defineWidget()` factory and the SDK types contributors build against
 * (IW-1c — Tier 3 authoring entry point).
 *
 * A widget kind is a self-contained module under `src/widgets/<kind>/`:
 *
 *   ```ts
 *   // src/widgets/_hello/index.tsx
 *   import { defineWidget } from '../_sdk/defineWidget';
 *   export default defineWidget({
 *     kind: '_hello',
 *     version: 1,
 *     meta: { title: 'Hello widget', answerProducing: false },
 *     render: ({ mount, config }) => {
 *       const p = document.createElement('p');
 *       p.textContent = 'Widget runtime alive · kind = ' + String(config.kind);
 *       mount.appendChild(p);
 *     },
 *   });
 *   ```
 *
 * **The `render` function runs inside the sandboxed iframe**, not the app
 * bundle. It is serialised to source via `Function.prototype.toString()` at
 * srcdoc build time and inlined into the boot `<script>`. This has two
 * consequences contributors must keep in mind:
 *
 *   - **`render` must be a pure function expression** — no captured
 *     closures, no app-bundle imports. The SDK provides everything via
 *     `ctx` (mount node, config, variables, hooks). IW-1c ships vanilla-DOM
 *     render functions; IW-2 lands React-in-sandbox so JSX widgets are
 *     possible.
 *   - **Anything `render` references must be on `ctx` or `globalThis`**.
 *     The sandbox has no app code loaded by design — that is the security
 *     boundary.
 *
 * The `meta` block is what the teacher gallery (Tier 1, IW-5) reads. The
 * Studio (Tier 2, IW-9/10) emits the same `WidgetSpec` shape from its
 * `studio-scene` kind, so the gallery never has to know which tier
 * authored a given widget.
 */

/**
 * Hooks + identity the SDK exposes inside the sandbox to a widget's
 * `render` call. Everything a widget can do — read its config, sample
 * variables, report an answer, request a resize — lives on this context.
 *
 * Adding a method here is an SDK-level change and bumps the protocol
 * version; widgets rely on stable hook signatures across builds.
 */
export interface WidgetContext {
  /** DOM node the widget renders into. Already in the sandbox body. */
  mount: HTMLElement;
  /** Per-student-substituted config (string `{{var}}` tokens already resolved server-side). */
  config: Record<string, unknown>;
  /** Sampled variable values for the student. May be empty. */
  variables: Record<string, number | string | boolean>;
  /** Absolute URL prefix for relative asset paths. */
  imageBase: string;
  /**
   * Answer-producing widgets call this to push their value to the host. The
   * grader then sees the value alongside any explicit answer fields. For
   * explanatory widgets (e.g. the legacy thermo sim) this is unused.
   *
   * Full grader wiring lands in IW-4; for IW-1c the call still flows through
   * the typed `value` message so the host bridge can observe it end-to-end.
   */
  reportValue: (value: unknown) => void;
  /**
   * Step-validating widgets (`step-solver`) call this when a student **commits**
   * a line, to report the *deterministic, in-sandbox* equivalence verdict for
   * that line vs the line above. The runtime serialises it to the typed `step`
   * message (GSV-4b); the host routes a `'bad'` step to the host-side AI coach.
   *
   * This is **not** an answer and **not** AI — the grade still flows only
   * through `reportValue`, and the verdict here is the same deterministic engine
   * that lights the live ✓/✗. Non-step widgets never call it.
   */
  reportStep: (step: {
    previous: string;
    current: string;
    verdict: 'ok' | 'bad' | 'neutral';
    reason: string;
  }) => void;
  /**
   * Manual resize request. The runtime also auto-emits a `resize` via
   * `ResizeObserver` whenever the body's size changes, so calling this
   * explicitly is rarely needed.
   */
  requestResize: () => void;
}

/** Metadata the teacher gallery + Studio surface read. */
export interface WidgetMeta {
  /** Human title shown in the gallery card. */
  title: string;
  /** Optional gallery-card blurb. */
  description?: string;
  /**
   * `true` if `render` ever calls `reportValue` — drives whether the
   * authoring UX wires it into the answer form (IW-4 / IW-5). Defaults to
   * `false`.
   */
  answerProducing?: boolean;
}

/**
 * JSON Schema describing the shape of a widget's `widget_config`. The
 * teacher gallery (IW-5) reads this to auto-generate the config form;
 * the backend's per-kind validator (future IW-3 follow-up) reads it
 * server-side. Typed as `Record<string, unknown>` here — the surface
 * shape is JSON-Schema draft 2020-12, but we don't ship a full schema
 * validator in the SDK; consumers narrow as needed.
 */
export type WidgetParamsSchema = Record<string, unknown>;

/**
 * Spec a contributor passes to `defineWidget`. The kind is the registry
 * key; `version` lets a question pin a specific behaviour so a widget
 * evolving doesn't break old content (cross-version migration is an IW-2
 * follow-up).
 */
export interface WidgetSpec {
  kind: string;
  version: number;
  meta: WidgetMeta;
  /**
   * Sandbox-side render function. Receives `ctx` (mount node + config +
   * variables + SDK hooks) and produces side effects on `ctx.mount`.
   *
   * SDK constraint: this function must be **self-contained** — no captured
   * closures, no imports — because it is serialised to source and inlined
   * into the iframe srcdoc. The SDK validates this at runtime to the extent
   * it can (typeof check + stringify); contributors are expected to keep
   * their renders pure.
   */
  render: (ctx: WidgetContext) => void;
  /**
   * Optional JSON Schema describing the widget's config shape. When
   * present, the teacher gallery (IW-5) auto-generates a form from it
   * and the live preview re-renders on every change. Import the
   * sibling `params.schema.json` with `import schema from
   * './params.schema.json'` and pass it here.
   */
  paramsSchema?: WidgetParamsSchema;
}

/**
 * What a widget module exports (default-exported by convention). The
 * registry stores `WidgetModule` instances keyed by `kind`; the host srcdoc
 * builder reads `render.toString()` off it to bake the boot script.
 */
export interface WidgetModule {
  readonly kind: string;
  readonly version: number;
  readonly meta: WidgetMeta;
  /** Source of the render function (already stringified) — what the boot script inlines. */
  readonly renderSource: string;
  /** JSON Schema for the config shape, if the widget declared one. */
  readonly paramsSchema?: WidgetParamsSchema;
}

/**
 * Factory contributors call from their widget module.
 *
 * Throws synchronously if the spec is malformed — kind must be a non-empty
 * string, version a positive integer, render an actual function. Fail-loud
 * here is better than the widget silently no-op'ing inside the sandbox.
 */
export function defineWidget(spec: WidgetSpec): WidgetModule {
  if (typeof spec.kind !== 'string' || spec.kind.length === 0) {
    throw new TypeError('defineWidget: `kind` must be a non-empty string.');
  }
  if (!Number.isInteger(spec.version) || spec.version <= 0) {
    throw new TypeError(`defineWidget(${spec.kind}): \`version\` must be a positive integer.`);
  }
  if (typeof spec.render !== 'function') {
    throw new TypeError(`defineWidget(${spec.kind}): \`render\` must be a function.`);
  }
  if (!spec.meta || typeof spec.meta.title !== 'string') {
    throw new TypeError(`defineWidget(${spec.kind}): \`meta.title\` is required.`);
  }

  return {
    kind: spec.kind,
    version: spec.version,
    meta: spec.meta,
    renderSource: spec.render.toString(),
    paramsSchema: spec.paramsSchema,
  };
}
