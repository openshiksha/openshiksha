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

*Next beat:* **DTB-2** — the `/ai/widget-authoring/` endpoint that turns the
plain-English prompt into a `{widget_kind, widget_config}`, always run through
this validator, with a deterministic stub fallback.
