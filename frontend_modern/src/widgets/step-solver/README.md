# `step-solver` widget (GSV-2b)

The Phase-2 **Guided Step-Validator** widget of the
[AI-Native Interactive Learning](../../../../docs/initiatives/ai-native-interactive-learning.md)
initiative.

The student solves the `prompt` equation/expression **one line at a time**. As
they type each line, a deterministic algebraic-equivalence engine — run **inside
the sandbox**, never AI — checks the new line against the line above and shows
live ✓ / ✗. The final line is reported through `ctx.reportValue` into the
existing per-subpart grader, exactly like `number-line`. **AI is nowhere near
this widget**: correctness is the same deterministic numeric-probing algorithm as
the backend GSV-1 engine.

## Config

| field | type | default | meaning |
|-------|------|---------|---------|
| `prompt` | string | `"x + 1 = 2"` | the starting equation/expression (fixed first line) |
| `label` | string | — | optional instruction shown above the steps |
| `maxLines` | integer 2–20 | `8` | max student step lines (excluding the prompt) |

## Why the engine is inlined

`render` is serialised via `Function.prototype.toString()` and inlined into the
network-less sandbox iframe — it cannot `import` the sibling
[`algebra.ts`](./algebra.ts) (the GSV-2a TS port of `apps/core/algebra.py`). So
this file inlines a faithful copy of that engine (the `function-plotter`
precedent). The two are kept honest by [`index.test.ts`](./index.test.ts), which
drives the widget over a curriculum battery and asserts its on-screen ✓/✗ matches
`checkStep` from `algebra.ts` **verdict for verdict** — the inlined copy can never
silently drift.

## Try it

```bash
cd frontend_modern
npm run widget:dev -- step-solver       # the sandboxed playground
npx vitest run src/widgets/step-solver  # unit tests (surface + executed render + anti-drift)
npx playwright test step-solver-grade   # real-sandbox render → live-check → grade signal
```

See [`docs/demo/golden-path.md`](../../../../docs/demo/golden-path.md) Beat 7.
