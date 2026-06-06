/**
 * Widget registry — the single source of truth for which widget kinds the
 * frontend bundle knows how to render.
 *
 * **Adding a widget kind = adding one entry here + one folder under
 * `src/widgets/<kind>/`.** That's the compounding goal: every later widget
 * (number-line, function-plotter, fraction-bar, the Studio's scene runner,
 * etc.) is one file + one schema, and the host doesn't need a code change
 * to render it.
 *
 * The server-side `KNOWN_WIDGET_KINDS` set (`backend/openshiksha/apps/core/widgets.py`)
 * mirrors these keys so the writable serializer rejects unknown kinds at
 * write time. The two registries are kept in sync by hand for now; IW-3's
 * per-kind JSON Schema validation will eventually make the backend
 * authoritative.
 */

import _hello from './_hello';
import type { WidgetModule } from './_sdk/defineWidget';

// widget:new inserts here — the IW-8 scaffolder appends new kinds above
// this comment so the diff is one line per widget.
export const widgetRegistry = {
  _hello,
} as const satisfies Record<string, WidgetModule>;

/** String-literal union of every registered kind. */
export type WidgetKind = keyof typeof widgetRegistry;

/** Lookup helper used by the host when building srcdoc for a `widget_kind`. */
export function getWidgetModule(kind: string): WidgetModule | undefined {
  return (widgetRegistry as Record<string, WidgetModule>)[kind];
}
