# `number-line` widget — the framework's first answer-producing widget

> The IW-4 proof that `ctx.reportValue` is wired through the host into
> the student's submission form. The student drags a point along an
> axis; the position (snapped to `step`) becomes their answer, graded
> by the existing numeric grader against `correct_answer`.

## What it does

Renders a labelled axis with tick marks and a draggable orange point.
Pointer events (mouse, touch, stylus) all share the same handler via
`setPointerCapture`, and arrow keys / Home / End nudge the point for
keyboard accessibility. Every change in position calls
`ctx.reportValue(value)`, which the host routes into the answer form.

The widget **does not** call `reportValue` on mount — the answer field
stays empty until the student actually interacts, so leaving a
question blank is still possible.

## Config

See [`params.schema.json`](./params.schema.json). All fields optional:

- `min` *(number, default `0`)* — left-end value
- `max` *(number, default `10`)* — right-end value
- `step` *(number > 0, default `1`)* — snap increment; also the
  keyboard arrow-key delta
- `initial` *(number, default `min`)* — starting position (no
  `reportValue` is emitted for this; see above)
- `label` *(string)* — optional caption rendered above the axis

## How the answer flows

```
            iframe (sandbox)              app DOM
   ┌──────────────────────────────┐
   │  number-line render         │
   │   └─ pointer drag → snap   │
   │      └─ ctx.reportValue(v) │  ──postMessage── ▶ createHostBridge.onValue(msg)
   │                              │
   └──────────────────────────────┘                    │
                                                       ▼
                                          InteractiveWidget.onValue prop
                                                       │
                                                       ▼
                                       QuestionCard.handleChange(subpart.id, v)
                                                       │
                                                       ▼
                                              Submission.answers[id] = v
                                                       │
                                                       ▼
                                              Server-side numeric grader
```

No parallel code paths. The grader sees the same shape it always has.

## Authoring tips

- Pair this with a numeric `correct_answer` (e.g. `{type: "numeric", answer: "42"}`).
- Set `step` to match the precision the answer needs. A `step` of `0.1`
  with `correct_answer = "3.14"` lets the student land exactly on 3.1
  or 3.2 but not 3.14, so authors should either match `step` to the
  answer or accept that fractional answers will be approximated.
- The widget surfaces the readout to the student in real time, so they
  always see the value they're submitting.
