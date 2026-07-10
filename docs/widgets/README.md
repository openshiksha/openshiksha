# Interactive Widgets — the contributor SDK

Widgets are the small, sandboxed interactives a question can embed — a
number line to drag, a piston to pump, a function to plot. This folder is the
**SDK guide**: everything an outside contributor needs to add a new *kind* of
widget to OpenShiksha.

> **Data vs. code — the one rule that governs this whole funnel.** A widget
> *kind* is **code** and ships **only** through normal pull-request review
> (this guide). The per-question `widget_config` a teacher fills in for an
> existing kind is **data** and travels the
> [content-pack pipeline](../../contrib/packs/README.md). New code never
> arrives through the content pipeline, and content never needs a code review.

## The path: propose → build → clear the bar

1. **[Propose it](../../.github/ISSUE_TEMPLATE/widget_proposal.md)** — open a
   *Widget proposal* issue first so we agree on scope (what it teaches,
   answer-producing vs. explanatory, config fields, a11y) before you write
   code. This saves you a rebuild.
2. **[Build your first widget](./build-your-first-widget.md)** — the ~10-minute
   loop: `npm run widget:new <kind>` scaffolds the folder + patches the
   registry, `npm run widget:dev -- <kind>` opens the sandbox playground, then
   you tighten `params.schema.json`, mirror the kind into the backend, and
   verify. Start here.
3. **[Anatomy of a widget](./anatomy.md)** — the canonical reference for the
   `defineWidget({ … })` contract, the `ctx` object, the **render sandbox
   constraints** (no closures, no app imports, self-contained function), the
   wire protocol, and the security model. Reach for this while you build.
4. **[Clear the review bar](./review-bar.md)** — the checklist your PR must
   pass: sandbox rules, both schema copies + the parity guard, answer-reporting
   precision, keyboard + ARIA accessibility, and test expectations. Read it
   *before* you open the PR, not after.

## What "one widget kind" costs

A kind is **one folder** under `frontend_modern/src/widgets/<kind>/` plus **one
line** in [`registry.ts`](../../frontend_modern/src/widgets/registry.ts) — and,
because validation runs on the server too, a mirrored entry in the backend's
`KNOWN_WIDGET_KINDS` and a byte-identical copy of your schema under
`backend/openshiksha/apps/core/data/widget_schemas/`. A CI parity test
(`TestWidgetSchemaParity`) fails the build if the two schema copies ever drift.
The scaffolder prints the backend steps on every run.

```
frontend_modern/src/widgets/<kind>/
├── index.ts            # default-exports defineWidget({ kind, version, meta, render })
├── params.schema.json  # JSON Schema for the teacher-facing widget_config
└── README.md           # what it does + delta from any legacy reference
```

## Worked examples (shipping today on `qa`)

Copy the closest one and trim — that is the fastest way to a correct widget.

| Kind | Type | What it shows |
|------|------|---------------|
| [`_hello`](../../frontend_modern/src/widgets/_hello/index.ts) | internal | The simplest possible widget — six lines of vanilla-DOM render. The framework's loop proof. (`_`-prefixed kinds are hidden from the teacher gallery.) |
| [`thermo-piston`](../../frontend_modern/src/widgets/thermo-piston/index.ts) | explanatory | SVG cylinder + piston; a slider drives ΔQ and buttons drive ΔW to *feel* ΔU = ΔQ − ΔW. Nothing is graded. |
| [`number-line`](../../frontend_modern/src/widgets/number-line/index.ts) | answer-producing | Drag a point on a number line; the snapped value is reported to the grader. The reference for `ctx.reportValue`. |
| [`function-plotter`](../../frontend_modern/src/widgets/function-plotter/index.ts) | explanatory | Plots a function over a domain from config. |
| [`fraction-bar`](../../frontend_modern/src/widgets/fraction-bar/index.ts) | explanatory | Partitioned bar for visualising fractions. |
| [`step-solver`](../../frontend_modern/src/widgets/step-solver/index.ts) | answer-producing | Student works a solution step by step; the final step is reported to the grader. |
| [`custom-html`](../../frontend_modern/src/widgets/custom-html/index.ts) | explanatory | Escape hatch: renders author-provided static HTML inside the same sandbox. |

For the framework's design rationale and roadmap, see the
[Interactive Widgets Framework initiative](../initiatives/interactive-widgets-framework.md).
