# 2026-06-06 — IW-7 · `custom-html` escape hatch + `interactive_html` deprecated

## Summary

The last piece of the Tier-3 contributor surface. Adds a `custom-html`
registry widget whose single config field is a raw HTML string —
renders inside the same sandboxed `<InteractiveWidget>` host every
other widget uses, re-executes inline `<script>` tags after innerHTML
insertion so authored interactivity actually runs.

With this kind in the registry, the legacy
`QuestionSubpart.interactive_html` field is **deprecated**: the
backend's `help_text` now flags it as such, and the going-forward
authoring path is `widget_kind='custom-html' + widget_config={html:
...}`. A one-shot migration command that moves the legacy thermo
question's HTML content onto the new path is the obvious follow-up but
deliberately out of scope here (the thermo question already renders on
the new `thermo-piston` widget; the raw `interactive_html` row content
will be cleared by that follow-up command).

## Classification

**New** (widget kind + showcase + tests) + small **Improve** (model
docstring deprecation flag + migration 0020).

## What changed

### Frontend
- **`src/widgets/custom-html/index.ts`** (new — scaffolded by `npm run
  widget:new custom-html` from IW-8-early, then fleshed out). The
  render function reads `ctx.config.html`, drops it in via
  `mount.innerHTML`, then walks the inserted subtree and replaces each
  `<script>` with a freshly-created node carrying the same attributes
  — the canonical pattern for re-executing scripts inserted by
  `innerHTML` (which leaves them inert). `async = false` keeps
  multi-script load order intact for vendor head chains. Falls back to
  a branded "no html field" notice when config is empty.
- **`src/widgets/custom-html/params.schema.json`** — `{ html: string }`,
  required. `additionalProperties: false`. Description calls out the
  admin-only gating.
- **`src/widgets/custom-html/README.md`** — what / when to use vs the
  three preferred paths (first-party widget → Studio scene → new
  Tier-3 kind) / how it relates to the legacy `interactive_html`
  surface.
- **`src/widgets/registry.ts`** — `custom-html` added (one line each
  for import + entry, via the IW-8 scaffolder anchors).
- **`src/features/design/DesignSystemPage.tsx`** — new "Interactive
  Widgets · IW-7 · custom-html" section embeds the kind with a tiny
  slider+readout HTML demo proving the inline script actually executes
  inside the sandbox.
- **`src/widgets/custom-html/custom-html.test.ts`** (new) — 7 vitest
  cases (identity + version, explanatory-not-answer-producing,
  admin-only label, registry round-trip, empty-config fallback,
  re-execution loop present in the inlined render source, script
  attributes preserved).

### Backend
- **`apps/core/models.py`** — `QuestionSubpart.interactive_html` and
  `is_interactive` flagged **DEPRECATED (IW-7)** in their `help_text`;
  `widget_kind`'s `help_text` updated to call out `custom-html` as the
  going-forward escape hatch.
- **`apps/core/migrations/0020_alter_questionsubpart_interactive_html_and_more.py`**
  (new) — Django picks up the `help_text` change as a `models.AlterField`,
  so this PR ships the resulting auto-migration. No schema change.

## Three-tier authoring surface — now complete

| Tier | Authoring path | Status |
|---|---|---|
| **1 — Configure** (every teacher) | First-party registry widget + auto-generated form | `thermo-piston` shipped; teacher gallery + form is IW-5 |
| **2 — Compose** (any teacher, in-app Studio) | Drag primitives onto a canvas → `widget_kind='studio-scene'` | Backend table (`TeacherWidget`) shipped #213; runtime + UI is IW-9 / IW-10 |
| **3 — Code** (contributor) | One file under `src/widgets/<kind>/` via `npm run widget:new` | **Complete after this PR.** SDK + scaffolder + anatomy doc + escape hatch all in place. |

The Tier-3 surface is now end-to-end usable: a contributor can scaffold
a kind in one command, the SDK guides their render constraints, and
even bespoke HTML one-offs that don't fit any of the structured paths
ship through `custom-html` instead of as a parallel raw-HTML field.

## Migration / data notes

The `interactive_html` deprecation is a **docstring change only** in
this PR — no data is touched. The legacy thermo question's row still
carries non-empty `interactive_html`, but the question already renders
through the new `thermo-piston` widget (set by the IW-3b migration
command #212) because `InteractiveWidget` prefers `kind` when both are
present.

The follow-up (`migrate_legacy_interactive_html` management command)
will: for any row with non-empty `interactive_html` *and* blank
`widget_kind`, set `widget_kind='custom-html'` + `widget_config={html:
<row.interactive_html>}` and clear `interactive_html`. That command
can land any time after this PR; nothing here blocks it.

## Tests

- Frontend `npm test` — 51 passed in `src/widgets/` (was 44 with IW-2 +
  IW-8-early; +7 custom-html cases). Type-check / lint / build all clean.
- Backend `pytest test_widget_fields.py` — 13 passed; `manage.py check`
  clean; new migration 0020 applies cleanly.

## Next

- **IW-4** — answer-producing widgets (`reportValue` → submission;
  `number-line` as the first example). The SDK already exposes
  `ctx.reportValue`; this just wires the host's `onValue` into the
  question answer form.
- **IW-5** — teacher gallery in `CreateQuestionPage` + JSON-Schema-driven
  config form + live preview. This is where Tier-1 "Configure" comes
  alive and where the `custom-html` admin gate becomes a real
  permission check, not just a label.
- *(Follow-up)* `migrate_legacy_interactive_html` management command —
  shifts legacy rows onto `widget_kind='custom-html'` and finally
  empties `interactive_html` so the field can be dropped in a future PR.
