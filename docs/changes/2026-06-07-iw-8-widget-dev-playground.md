# 2026-06-07 - IW-8 · Widget dev playground

## Summary

Completes the deferred half of IW-8. Contributors can now scaffold a widget and
open it directly in a focused sandbox playground instead of wiring a full
question or browsing the whole `/design` catalogue.

## What changed

- **`/widgets/dev`** - new unauthenticated contributor route with:
  - registry-backed widget picker
  - metadata badges
  - config JSON editor seeded from `params.schema.json` defaults
  - variables JSON editor
  - live `<InteractiveWidget />` sandbox preview
  - last-reported-value readout for answer-producing widgets
- **`npm run widget:dev -- <kind>`** - launcher that starts Vite and opens the
  playground at `/widgets/dev?kind=<kind>`.
- **Docs** - new [`docs/widgets/build-your-first-widget.md`](../widgets/build-your-first-widget.md)
  tutorial, plus links from `docs/widgets/anatomy.md` and
  `frontend_modern/src/widgets/README.md`.
- **Initiative status** - `docs/initiatives/STATUS.md` now reflects that
  IW-1 through IW-8 are done and hands the next routine to IW-9 proper.

## Test plan

- `npm test -- --run src/features/widgets/WidgetDevPage.test.tsx scripts/create-widget.test.mjs`
- `npm run type-check`

## Next

Start **IW-9**: ship `studio-scene`, the safe formula evaluator, primitive
scene rendering, scene schema validation, and TeacherWidget API permissions so
hand-authored Studio JSON can render through the sandbox before the visual
builder lands in IW-10.
