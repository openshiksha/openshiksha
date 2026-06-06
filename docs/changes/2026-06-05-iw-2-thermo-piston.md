# 2026-06-05 — IW-2 · `thermo-piston` widget

## Summary

Ships the first **non-stub** widget on the Interactive Widgets Framework
— a faithful re-implementation of the Class-11 Thermodynamics piston /
First-Law sim from Cabinet question `1/1/11/3/44/22`. Same physics
(ΔU = ΔQ − ΔW), same visual story (slider + piston + readouts), but on
the SDK runtime instead of jQuery / jQuery-UI / Bootstrap 3 / inline
`<script>` — ~280 KB of vendor head dropped for ~3 KB of vanilla
DOM + SVG.

The backend defaults (IW-3b's `migrate_legacy_thermo_widget` command,
#212) are updated to match the widget's real config schema. Run that
command now and the legacy thermo question renders end-to-end on the
new path.

## Classification

**Port** (legacy widget → SDK widget) + **Improve** (kinetic-theory
particles, brand-on tokens, vendor surface removed).

## What changed

- **`frontend_modern/src/widgets/thermo-piston/index.ts`** (new) —
  `defineWidget({ kind: 'thermo-piston', ... })`. Vanilla DOM + SVG
  inside the sandbox: cylinder walls, gas region, piston slab + rod,
  heat strip, controls (heat slider, ▲ expand / ▼ compress buttons,
  reset), live formula panel.
- **Kinetic-theory particles** — 16 gas molecules vibrate on a
  `requestAnimationFrame` loop. Amplitude, oscillation speed, and
  radius are all driven by internal energy
  `u = q − w`, normalised against ±200 J and clamped to a 0.4–6 px
  jiggle. Heat in → faster, bigger particles; heat out → calmer,
  smaller. Compression with no heat (W < 0, Q = 0) still increases ΔU,
  so the particles speed up exactly as the First Law predicts.
- **Piston floor / ceiling** — `PISTON_Y_MIN` (40) and `PISTON_Y_MAX`
  (200) clamp the slab so it can never dip past the cylinder bottom
  (y = 250). The gas region is `Math.max(36, …)` so there is always
  ≥36 px of room for particles to jiggle even at extreme negative
  work. No more clipping under the cylinder.
- **`frontend_modern/src/widgets/thermo-piston/params.schema.json`**
  (new) — JSON Schema for `heatMin`, `heatMax`, `workMax`, `workStep`,
  `title`. Includes deprecated-but-accepted `initialVolume` and
  `maxHeat` keys so configs stamped by the IW-3b migration command
  (#212) don't fail validation later.
- **`frontend_modern/src/widgets/thermo-piston/README.md`** (new) —
  anatomy of a widget worked from this one; behaviour summary + delta
  from the legacy.
- **`frontend_modern/src/widgets/registry.ts`** — `thermo-piston`
  registered alongside `_hello`. The `widget:new inserts here` anchor
  used by the upcoming IW-8 scaffolder is preserved.
- **`backend/openshiksha/apps/core/management/commands/migrate_legacy_thermo_widget.py`**
  — `DEFAULT_THERMO_CONFIG` updated from the IW-3b placeholders
  (`initialVolume`, `maxHeat`) to the widget's real keys (`heatMin`,
  `heatMax`, `workMax`, `workStep`). Re-running the command on rows
  already stamped is still a no-op (idempotency check on `widget_kind`).
- **`backend/openshiksha/apps/core/tests/test_widget_fields.py`** —
  the `test_command_stamps_widget_kind` case updated to assert the new
  bounds.
- **`frontend_modern/src/features/design/DesignSystemPage.tsx`** —
  new "Interactive Widgets · IW-2" showcase section embedding
  `thermo-piston` with sample `variables: { k: 80, j: 30 }` so the
  "your question values" hint surfaces.
- **Tests** — `thermo-piston.test.ts` (8 cases) asserting kind
  identity, registry round-trip, render-source contents (First-Law
  formula present, no jQuery / `$()` / glyphicon, `requestAnimationFrame`
  particle loop present, `PISTON_Y_MIN/MAX` clamps + 36 px gas floor
  present). Backend `test_widget_fields.py` continues to pass.

## Why vanilla DOM and not React-in-sandbox

The runtime that wraps `render` (`_sdk/runtime.ts`) does not bootstrap
React inside the sandbox. Pulling React in would mean shipping
~100 KB of vendor head per widget srcdoc — exactly what we just got rid
of by porting off jQuery. The piston widget doesn't need JSX
ergonomics; the slider + buttons + readouts + SVG fit cleanly in
vanilla DOM with the SDK hooks. JSX-driven widgets remain an option for
the future (IW-6 or later); for now this proves a real, polished widget
ships through the framework without inflating the bundle.

## What's still legacy

The thermo question's `interactive_html` field is still populated on
the row — IW-7 deprecates and eventually drops it. Until then, both
paths coexist; the renderer (`InteractiveWidget`) prefers `kind` when
both are present, so a question stamped with `widget_kind="thermo-piston"`
by the migration command (#212) now renders through the new path
automatically.

## Tests

- Frontend: `npm test` — **131 passed** (10 protocol + 16 host + 6
  defineWidget + 4 registry + 8 thermo-piston + 4 legacy InteractiveWidget +
  others). Type-check / lint / build clean.
- Backend: `pytest openshiksha/apps/core/tests/test_widget_fields.py` —
  13 passed.

## Next

- **IW-8-early** — `npm run widget:new <kind>` scaffolder + `/widgets/dev`
  playground + `docs/widgets/anatomy.md`. The scaffolder's anchor
  comment is already in place in `registry.ts`.
- **IW-7** — `custom-html` registry kind for the escape hatch +
  `interactive_html` deprecated. After IW-7 the legacy thermo's
  `interactive_html` row content can be cleared and the kind-based
  path is the only path.
