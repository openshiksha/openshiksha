# `function-plotter` widget

An **explanatory** widget that plots `y = f(x)` over a configurable
domain. The teacher authors an expression in `x`; the widget samples it
across `[xMin, xMax]` and draws the curve inside an SVG axis with light
grid + bold zero lines.

## What it does

- Renders an axis (default `[-5, 5] × [-5, 5]`)
- Compiles the `expr` config with a small recursive-descent evaluator
  (numbers; `x`, `pi`, `e`; `+ - * / **` with standard precedence;
  unary minus; `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `log`,
  `ln`, `log10`, `exp`, `sqrt`, `abs`, `floor`, `ceil`, `round`,
  `pow`, `min`, `max`)
- Samples the function 200 times across the domain and draws a polyline
- Breaks the polyline on NaN / ∞ samples so vertical asymptotes don't
  smear across the plot

If `expr` is malformed (unknown identifier, missing `)`, etc.), the
widget renders a friendly red error band instead of silently plotting
nothing.

## Why a hand-rolled parser instead of `Function(expr)` or `eval()`

The render runs inside the sandboxed iframe, so the sandbox boundary
already protects the host — but `Function()` and `eval()` are noisy
patterns we'd rather not normalise in widget source. A contributor
copy-pasting from this file shouldn't end up shipping `Function()` in
their widget either. The parser is ~120 lines and only handles math.

## Config

See [`params.schema.json`](./params.schema.json). All fields optional:

- `expr` *(string, default `"x**2"`)* — the math expression
- `xMin`, `xMax` *(number, default −5 / +5)* — x-axis bounds
- `yMin`, `yMax` *(number, default −5 / +5)* — y-axis bounds
- `title` *(string)* — optional caption rendered above the plot

## Not answer-producing

The widget never calls `reportValue`. The student types the numeric or
MCQ answer into the usual field below; the widget is there to make the
question's geometry obvious.
