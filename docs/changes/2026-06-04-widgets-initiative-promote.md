# Interactive Widgets Framework — Initiative promotion

**Classification:** Docs.

## Summary
With V2 "Chalk & Unlock" essentially closed (#207 wrapped the last
open ~ item with the seed-baselines workflow), promote the
[Interactive Widgets Framework](../initiatives/interactive-widgets-framework.md)
from ⚪ Proposed to 🟢 **#1 active**. The M7-11 sandbox primitive
(`InteractiveWidget.tsx`, #132) already exists as the seed runtime, so the
initiative's gate condition is met.

## Files changed
- `docs/initiatives/interactive-widgets-framework.md` — full rewrite of the
  proposed doc into an active backlog: status flipped, DX-first principle
  added (principles #3 and #4), `defineWidget()` API made explicit, IW-8
  "Newcomer kit" milestone added (`npm run widget:new` scaffold + dev
  playground + 10-min tutorial), each IW-N increment broken down to
  PR-sized work with named files and DoD.
- `docs/initiatives/STATUS.md` — Widgets Framework at priority 1; V2
  marked ✅ Closing with the two one-click activations called out; Cabinet
  Data Fidelity noted as the M7-11 seed.
- `docs/daily-plans/2026-06-05-plan.md` — **new**. The next routine run's
  plan: ship IW-1 as 3 atomic PRs (IW-1a protocol types, IW-1b host
  module, IW-1c runtime + hello-widget + `/design` preview). Each item
  names the exact files, DoD, and how to verify.

## Why this shape
The user-stated requirements were "must be extensible, feel natural, easy
hooks to build things quickly and nicely to attract newer people." The
backlog encodes this:

- **One file per widget kind** (principle #4, IW-2 DoD): a widget is
  `index.tsx` calling `defineWidget(...)` plus a JSON Schema. No string
  IDs duplicated, no separate registration step.
- **`npm run widget:new <kind>`** (IW-8): scaffolds the boilerplate so a
  first-time author skips it entirely.
- **Hot-reloading dev playground at `/widgets/dev`** (IW-8): see your
  widget render before it ever touches a question.
- **10-minute tutorial** (IW-8 deliverable): the reviewer-tested path to a
  first ship. Each pass tightens the docs.
- **V2-native inside the sandbox** (principle #9): widgets read as one
  product, not a third-party embed.

## How the routine picks this up
- The plan routine ([`~/.claude/scheduled-tasks/openshiksha-plan/SKILL.md`](../../../.claude/scheduled-tasks/openshiksha-plan/SKILL.md))
  reads `docs/initiatives/STATUS.md` to find the top active initiative,
  then writes a daily plan with 3–5 PR-sized batch items.
- `STATUS.md` now points at the Widgets Framework as priority 1, with the
  IW-1 increment explicitly named.
- For tomorrow's first run a daily plan already exists
  (`docs/daily-plans/2026-06-05-plan.md`) so the plan routine can either
  pick it up directly or refresh it; either path lands on IW-1 first.
- The execute routine then runs the batch — each item is concrete enough
  to ship without further decisions.

## Verification
- Docs-only change; no code touched.
- All cross-references checked (`STATUS.md` ↔ initiative doc ↔ daily plan ↔
  M7-11 commit `4af87a9a` / PR #132 ↔ `InteractiveWidget.tsx`).

## Next
The IW-1 batch lands in tomorrow's routine run as PRs 1 / 2 / 3 of the
Widgets Framework's progress ledger.
