# Build your first widget

This is the 10-minute Tier-3 loop for contributors: scaffold a widget, open it
in the sandbox playground, edit the config, then wire the kind into backend
validation.

## 1. Scaffold

```bash
cd frontend_modern
npm run widget:new color-picker
```

The script creates:

- `src/widgets/color-picker/index.ts`
- `src/widgets/color-picker/params.schema.json`
- `src/widgets/color-picker/README.md`

It also inserts the import and registry entry in `src/widgets/registry.ts`.

## 2. Open the playground

```bash
npm run widget:dev -- color-picker
```

That launches Vite at `/widgets/dev?kind=color-picker`. The playground reads
the live registry, seeds config JSON from `params.schema.json` defaults, and
renders the widget through the same sandboxed `<InteractiveWidget />` host that
students use.

Use the left panel to edit:

- **Config JSON** — the widget's `ctx.config`.
- **Variables JSON** — the widget's `ctx.variables`, useful for trying values
  that would normally be substituted per student.

Answer-producing widgets can call `ctx.reportValue(value)`; the playground
shows the last reported value under the preview.

## 3. Implement the widget

Open `src/widgets/color-picker/index.ts` and replace the generated starter implementation. Keep
the render function self-contained:

- Do not capture variables from the app bundle.
- Do not import app code into the render function.
- Read config from `ctx.config`.
- Report answers with `ctx.reportValue(value)` only if `meta.answerProducing`
  is true.

## 4. Tighten the schema

Edit `params.schema.json` so the teacher gallery can generate a usable form.
Prefer explicit defaults; the playground uses those defaults for its initial
config.

## 5. Add backend validation

Add the new kind to `KNOWN_WIDGET_KINDS` in
`backend/openshiksha/apps/core/widgets.py`. Without that mirror entry, the
teacher write API rejects the kind even though the frontend can render it.

Then copy your `params.schema.json` to
`backend/openshiksha/apps/core/data/widget_schemas/<kind>.schema.json` (a
byte-identical copy). The backend validates every `widget_config` against it
(DTB-1), so a malformed config is rejected with a `400` at write time instead of
breaking the sandbox. A parity test fails CI if the vendored copy drifts from the
frontend source.

## 6. Verify

```bash
npm run type-check
npm test -- --run src/widgets registry.test.ts
```

For a full reference on `defineWidget`, sandbox constraints, and the message
protocol, see [`anatomy.md`](./anatomy.md).
