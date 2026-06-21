# `thermo-piston` widget

> First widget on the Interactive Widgets Framework after `_hello`.
> Re-implementation of Cabinet question `1/1/11/3/44/22` (Class-11
> Thermodynamics, First Law of Thermodynamics).

## What it does

An **explanatory** widget: the student manipulates a piston-in-cylinder
system and watches `ΔU = ΔQ − ΔW` update live.

- Heat slider → ΔQ (Joules, range from `heatMin` to `heatMax`)
- Up / down buttons → ΔW (Joules, ±`workMax`, `workStep` per click)
- Formula readout shows ΔQ, ΔW and the derived ΔU
- Piston SVG rises and falls with work, **clamped** so it can never dip
  past the cylinder floor — the gas region keeps at least ~36 px of
  vertical room so the simulation never collapses on itself
- 16 gas particles inside the cylinder jiggle on a `requestAnimationFrame`
  loop. Amplitude + speed + radius all scale with internal energy
  `ΔU = ΔQ − ΔW` — the kinetic-theory intuition that hotter gas has
  larger ⟨KE⟩ comes through visually. Heat in → particles bigger and
  faster; heat out → particles calm and shrink; compress without heat →
  ΔU goes up too (work-in heating) so the particles speed up exactly as
  the First Law predicts
- Heat strip recolours with sign of Q (red ↔ blue ↔ neutral)

It does **not** call `reportValue` — the student types the numeric
answer into the regular numeric answer field below the widget, exactly
as in the legacy flow. The widget just builds intuition.

## Anatomy of a widget (this file as worked example)

This is what every widget folder ends up looking like:

```
src/widgets/thermo-piston/
├── index.ts            # default-exports defineWidget({ kind, version, meta, render })
├── params.schema.json  # JSON Schema for the per-question config the teacher fills in
└── README.md           # this file — what it does, what it expects, what changed
```

1. **`defineWidget(...)`** in `index.ts` registers the kind + metadata
   the gallery surfaces, and ships the `render` function that runs
   **inside the sandbox**. Render constraints (no closures, no app-bundle
   imports, self-contained expression) are spelled out in
   `src/widgets/README.md`.

2. **`params.schema.json`** is the contract with the teacher-authoring
   UX (IW-5). Every key the `render` reads off `ctx.config` should show
   up here with a description + default so the auto-generated form is
   useful.

3. **`README.md`** is what someone opens when they hit your widget in
   the registry and ask "what's this and how does the question
   actually use it?". Keep it short — physics / behaviour / what
   you skipped from a legacy reference if any.

## What changed from the legacy

| Concern | Legacy | This widget |
|---|---|---|
| Vendor head | jQuery 3.6 + jQuery-UI 1.13 + Bootstrap 3 glyphicons (~280 KB) | None — vanilla DOM + SVG (~3 KB) |
| Embedded `<script>` | Raw in `interactive_html`, runs in the same iframe srcdoc | None — render runs through the SDK runtime boot |
| Image assets | `8.gif` (gas), `7.gif` (fire), `9.png` (ice) via Cabinet `#{...}#` | Skipped (flat colours). IW-6 polish can re-add via `ctx.imageBase`. |
| Variable substitution | `_{k}_` / `_{j}_` tokens inlined into HTML at delivery | `ctx.variables.k` / `.j` exposed by the croupier; surfaced as a small "your question values" hint |
| Slider | jQuery-UI `slider({min:-200,max:200,value:0})` | `<input type="range" min={heatMin} max={heatMax}>` |
| Piston motion | Hold-mousedown timer (`setTimeout` 20 ms) ratcheting Y by ±1 | `▲ expand` / `▼ compress` buttons stepping by `workStep` Joules per click |

The **physics is identical** (ΔU = ΔQ − ΔW). The **delivery** is the
only thing that changed.

## Default config (matches the legacy bounds)

```json
{
  "heatMin": -200,
  "heatMax": 200,
  "workMax": 200,
  "workStep": 5,
  "title": "Thermodynamics — piston & First Law"
}
```

`initialVolume` and `maxHeat` from the original IW-3b migration default
(#212) are accepted but ignored — the schema flags them as deprecated.
A follow-up may drop them from the migration command once #212 has
fully rolled out.
