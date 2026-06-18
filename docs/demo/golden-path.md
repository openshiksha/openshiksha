# Golden-Path Demo — AI-Native Interactive Learning

> The ~2-minute demo this initiative assembles, one iron-clad beat at a time.
> Each beat is **(a) not in the market, (b) tactile and verifiable on screen, and
> (c) iron-clad by construction.** Beats land here as the
> [`openshiksha-ai-features`](../initiatives/ai-native-interactive-learning.md)
> routine ships the increments behind them.

**The story:** a teacher types a plain-English description of a manipulative — *"a
number line where students mark ¾"* — and a **validated, sandboxed, auto-graded
interactive widget** appears in the live preview, ready to attach to a question. A
student then drags the point and is graded by the deterministic per-subpart
grader. AI **authored** the widget; it never **graded** it.

---

## Beat 0 — The guardrail keystone (DTB-1) · *foundation, off-screen*

Before any AI emits a widget, the platform can already **prove a widget config is
well-formed**. Every `widget_config` written through the teacher API is validated
against its kind's JSON Schema on the server — types, bounds, enums, required
fields, and `additionalProperties: false`. A malformed config is rejected with a
clear `400` *at write time*, never discovered later inside the sandbox.

This is the safety floor the whole demo stands on: when DTB-2's AI proposes a
`{widget_kind, widget_config}`, it is run through this exact validator before it
is ever rendered or stored. **Malformed AI output cannot escape into the runtime
or the DB.**

**Why it's iron-clad:** the schemas are *data*, not code; correctness is a
deterministic schema check (no AI in the path); a kind with no vendored schema or
an unreadable file degrades to floor-only validation rather than a 500; and
`{{var}}` croupier bindings are first-class, so variable-randomized widgets still
validate.

**Verify it (no UI yet):**

```bash
cd backend
# Valid + invalid config per kind, the {{var}} tolerance, and the deterministic
# fallback path are all exercised here:
./venv/Scripts/python.exe -m pytest \
  openshiksha/apps/core/tests/test_widget_fields.py -q --no-cov
```

Or against the live API — a bogus config is refused:

```jsonc
// POST /api/v1/questions/  (teacher auth) with a subpart:
{ "widget_kind": "number-line", "widget_config": { "step": 0 } }
// → 400  "number-line config field 'step': 0 is less than or equal to ... 0"
```

while a real one (`{"min": 0, "max": 1, "step": 0.25, "label": "Mark ¾"}`) is
accepted.

---

## Beat 1 — Describe-to-Build, the endpoint (DTB-2) · *the engine, off-screen*

Now the platform can turn a teacher's sentence into a widget. `POST
/api/v1/ai/widget-authoring/` with `{"description": "a number line where students
mark 3/4"}` returns a **validated** proposal:

```jsonc
// → 200
{
  "widget_kind": "number-line",
  "widget_config": { "min": 0, "max": 1, "step": 0.25, "label": "Mark the value" },
  "model_used": "claude-sonnet-4-6",
  "ai_available": true,
  "repaired": false
}
```

The endpoint grounds the model in the **real, vendored schemas** of the four
authorable kinds (`number-line`, `fraction-bar`, `function-plotter`,
`thermo-piston`) and asks only for *config data* — never code. Whatever the model
returns is run through the Beat 0 guardrail before it leaves the server:

1. **Valid** → returned as-is (`ai_available: true`, `repaired: false`).
2. **Out of bounds / unknown keys / bad enum** → one deterministic **clamp-repair**
   pass (e.g. `denominator: 1000 → 40`, unknown keys dropped) then re-validated
   (`repaired: true`).
3. **Un-salvageable** (wrong kind, non-object config) **or no LLM provider** → the
   kind's **deterministic safe default**, honestly flagged `ai_available: false`
   so the UI badges it `Auto-…`, never as a real generation.

So the response is **always schema-valid by construction**, and a missing key /
dead provider yields a working widget instead of a `500`. The grader is never
touched — AI authors, it does not grade.

**Why it's iron-clad:** AI runs on the host, never in the sandbox (principle 1);
its output is config-as-data, schema-validated before render/store (3); there is a
deterministic clamp-repair *and* a safe-default fallback, both tested (4); the
prompt is grounded in the actual kind schemas (5); provenance is honest via
`ai_available` / `model_used` (6).

**Verify it (no UI yet):**

```bash
cd backend
# Real path, clamp-repair path, un-salvageable path, and the no-provider
# fallback — each asserted to return a schema-valid config:
./venv/Scripts/python.exe -m pytest \
  openshiksha/apps/ai/tests/test_widget_authoring.py -q --no-cov
```

Or against the live API as a teacher — note `ai_available: false` when no LLM key
is configured, with a still-valid default config you can attach immediately.

*Next beat:* **DTB-3** — the "Describe a widget" prompt box in `WidgetGalleryPanel`
that calls this endpoint and renders the proposal in the **live sandbox preview**,
editable via the existing schema form. The on-screen wow.
