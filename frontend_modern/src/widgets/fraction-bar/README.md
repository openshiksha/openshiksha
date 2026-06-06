# `fraction-bar` widget

An **explanatory** primary-school widget showing a fraction
`numerator / denominator` as a horizontal bar split into equal
segments with the filled portion highlighted in brand orange.

## What it does

Renders a bar with `denominator` equal segments; the first `numerator`
of them are shaded. Two display modes:

- **`shaded`** (default) — bar only. Use this when the question asks
  the student to *name* the fraction; the widget hides the numerals so
  the answer isn't given away by the image.
- **`labelled`** — bar plus a small `n/d` caption underneath. Use this
  in hints / worked solutions where the value should be visible.

Inputs are clamped to sane bounds:

- `denominator` is rounded to an integer and capped at 40 so segments
  stay visible (a 1-segment bar still renders if the teacher really
  wants it)
- `numerator` is clamped to `[0, denominator]` — a "5/4" mistake just
  shows a fully-shaded bar

## Config

See [`params.schema.json`](./params.schema.json). All fields optional:

- `numerator` *(number, default 1)*
- `denominator` *(number, default 4)*
- `mode` *(`"shaded"` | `"labelled"`, default `"shaded"`)*
- `title` *(string)* — optional caption above the bar

## Not answer-producing

The widget never calls `reportValue`. The student types the fraction
(or selects the MCQ option) into the usual answer field below.
