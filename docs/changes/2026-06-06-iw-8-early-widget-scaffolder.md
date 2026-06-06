# 2026-06-06 — IW-8-early · `npm run widget:new` scaffolder + anatomy doc

## Summary

The DX win the [Interactive Widgets Framework](../initiatives/interactive-widgets-framework.md)
backlog says to ship right after IW-2. Adding a new widget kind is now
a single command (`npm run widget:new <kind>`) instead of "copy
`_hello`, rename three identifiers, patch the registry in two places,
remember the JSON-Schema field shape". Every later widget — IW-4's
`number-line`, IW-6's `function-plotter` + `fraction-bar`, IW-7's
`custom-html` — is now genuinely cheap.

The canonical SDK reference (`docs/widgets/anatomy.md`) lands alongside
the scaffolder so the file a newcomer hits first explains the framework
in one place.

## Classification

**New.** Pure DX surface; no production code path changes.

## What changed

- **`frontend_modern/scripts/create-widget.mjs`** (new) — Node script
  invoked via `npm run widget:new <kind>`. Validates the slug
  (lowercase, hyphen-separated, leading-underscore allowed for
  framework-internal kinds), refuses duplicates (folder *and* registry
  key), scaffolds `index.ts` + `params.schema.json` + `README.md` from
  templates, then patches `src/widgets/registry.ts` at the
  `widget:new import anchor` / `widget:new entry anchor` comments. The
  CLI output ends with the one remaining manual step (the server-side
  `KNOWN_WIDGET_KINDS` mirror in `backend/openshiksha/apps/core/widgets.py`).
- **`frontend_modern/src/widgets/registry.ts`** — old single `widget:new
  inserts here` comment replaced by two **named** anchors so the patch
  is robust: one for imports (column 0), one for entries (inside the
  `widgetRegistry` object). Behaviour unchanged.
- **`frontend_modern/scripts/create-widget.test.mjs`** (new) — 11
  vitest cases covering `validateKind` (all rejection branches),
  `kindToIdentifier` (camelCase + leading-underscore preservation),
  `patchRegistry` (import + entry placement, prior entries preserved,
  missing-anchor throws).
- **`frontend_modern/package.json`** — adds the `widget:new` script.
- **`frontend_modern/vite.config.ts`** — extends the vitest `include`
  pattern with `scripts/**/*.{test,spec}.mjs` so the scaffolder tests
  run with the regular `npm test` pass.
- **`frontend_modern/src/widgets/README.md`** — "Adding a new widget
  kind" section rewritten around the scaffolder; pointer to the new
  anatomy doc.
- **`docs/widgets/anatomy.md`** (new) — canonical SDK reference
  worked from `_hello` and `thermo-piston` as examples. Covers
  `defineWidget` API, `ctx` hooks, the three render-function
  constraints that trip everyone up (no captured closures, no
  app-bundle imports, self-contained literal), the wire protocol, the
  security model, and the manual server-side registry mirror.

## How it works (one paragraph)

The registry has two short anchor comments — `widget:new import anchor`
above the type import, `widget:new entry anchor` inside the
`widgetRegistry` object. The script reads `registry.ts`, asserts both
anchors exist, then string-replaces each anchor with `<new-line>\n<original-anchor>`.
That guarantees the diff is exactly one import line + one entry line +
nothing else. If the anchors are missing (someone hand-deleted them)
the script throws with a clear message instead of silently producing a
broken registry.

## Why not a `/widgets/dev` playground in this PR

Plan-2 calls out a `/widgets/dev` route as an optional follow-up.
Skipped here to keep the PR atomic — the scaffolder is the keystone DX
win, and the `/design` page already mounts every registered kind for
quick visual checks. Playground can be its own slice once we have
several widgets to flip between.

## Tests

- `npm test` — **144 passed** (was 131; +11 scaffolder cases + a couple
  of other small additions). Type-check / lint / build all clean.
- End-to-end sanity: `node scripts/create-widget.mjs sample-test`
  produces a compiling widget with correct 2-space indent in the
  registry; `npm run type-check` passes on the scaffolded tree.

## Next

- **IW-7** — `custom-html` registry widget for the escape hatch +
  `interactive_html` deprecated. Once that lands the legacy thermo's
  raw HTML row content can be cleared and the kind-based path is the
  *only* path.
- **IW-4** — answer-producing widgets (`reportValue` → submission;
  `number-line` as the first example). Use the scaffolder to spin up
  the folder.
