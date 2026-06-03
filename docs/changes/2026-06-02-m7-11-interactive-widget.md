# M7-11 — Interactive-widget question support (sandboxed render)

## Summary

Rescues the **one** Cabinet question whose interactivity the M7-04 DOMPurify
path was silently killing: the Class 11 Physics Thermodynamics piston/heat
First-Law simulation (`raw/1/1/11/3/44/22.json`) — an SVG piston-cylinder with a
jQuery-UI heat slider and press-and-hold piston arrows driving a live
`ΔU = ΔQ − ΔW` readout. The importer now **preserves** authored interactive HTML
(`<script>`/event handlers) instead of dropping it, and the student UI renders it
inside a **sandboxed iframe** so the authored JS runs safely.

## Classification

**New** — additive content class (not part of the original Cabinet Data Fidelity
DoD). This is the *seed* for the future
[Interactive Widgets Framework](../initiatives/interactive-widgets-framework.md).

## Security model (the core of this change)

- `interactive_html` is stored **raw on purpose** (it contains `<script>`). It is
  **never** rendered into the app DOM or via `dangerouslySetInnerHTML`.
- It is delivered **only** to `<iframe sandbox="allow-scripts" srcDoc=…>` —
  deliberately **without** `allow-same-origin`. That combination would let the
  untrusted authored script read the app's cookies/storage/parent DOM; never add
  it. The opaque-origin iframe is the trust boundary that lets us run authored JS.
- Token resolution happens **before** the sandbox: image `#{…}#` tokens → absolute
  URLs at import; `{{var}}` → per-student values in the serializer. The sandbox
  has no access to the app's substitution logic.

## Backend (6a)

- **Model** (`QuestionSubpart`): `is_interactive` (bool) + `interactive_html`
  (TextField). Migration `0017`. Help-text documents the no-DOM-injection invariant.
- **Importer**: `is_interactive_html()` detects `<script>`/`on*=`; for those
  subparts it stores the raw HTML (variable tokens → `{{var}}`, image `#{…}#`
  resolved to **bare** URLs via `resolve_inline_image_urls`) in `interactive_html`,
  sets `is_interactive=True`, and puts a **script-free** `strip_interactive()`
  fallback in `question_text`. New `interactive` stat.
- **Serializer** (student): exposes `is_interactive` + `interactive_html` and
  substitutes the same per-student sampled values into the widget HTML.
- **Admin**: both fields shown on the subpart inline.

Validated on the real corpus: `import … ` reports `interactive=1`; the stored
thermo subpart has `is_interactive=True`, `<script>` in `interactive_html` (with a
resolved raw-GitHub gif URL and `{{var}}` tokens), and **no** `<script>` in
`question_text`.

## Frontend (6b)

- **`shared/ui/InteractiveWidget.tsx`**: renders the widget in a sandboxed iframe.
  `srcDoc` wraps the HTML in a minimal document loading pinned jQuery + jQuery-UI
  (+ jQuery-UI CSS) and Bootstrap-3 glyphicons (the 2015-era widgets depend on
  them). Self-sizes via `postMessage` (height reported from inside the frame;
  parent trusts only its own iframe's `contentWindow`). Falls back to
  `RichContent(question_text)` when there's no widget HTML.
- **`QuestionCard`**: when `subpart.is_interactive && interactive_html`, renders
  `InteractiveWidget` instead of the `RichContent` path. The numeric answer input
  is unchanged and lives outside the iframe (graded exactly as before — the iframe
  is purely the explanatory simulation).
- Exported from `shared/ui` and demoed on the **`/design`** route.

### Verified in the running stack

Loaded `/design` in the Docker frontend: the widget renders (slider + live
readout), the iframe has `sandbox="allow-scripts"` and **no** `allow-same-origin`,
and the parent's `contentDocument` access returns `null` — confirming the
isolation boundary. Screenshot: `docs/initiatives/screenshots/m7-11-interactive-widget.png`.

## Tests

- Backend (`test_import_cabinet.py`): detection (`is_interactive_html` /
  `strip_interactive`), `convert_subpart` flags interactivity + keeps `{{var}}` in
  `interactive_html` while keeping `question_text` script-free, and a DB test on
  the interactive fixture (Q1008) asserting `is_interactive`, `<script>` preserved,
  image token resolved to a bare URL, and a script-free fallback. Count assertions
  bumped 6 → 7 for the new fixture.
- Frontend (`InteractiveWidget.test.tsx`): sandbox has `allow-scripts` but **not**
  `allow-same-origin`; `srcDoc` carries the resolved HTML + jQuery/jQuery-UI; the
  raw widget HTML is **not** injected into the app DOM; empty html → sanitised
  fallback, no iframe.

Full suites green: backend, frontend (50 tests), type-check, lint, build.

## Hardening follow-ups (tracked for the Interactive Widgets Framework)

- Add SRI integrity hashes to the pinned CDN libs (or vendor them locally). The
  sandbox-without-same-origin is the primary boundary; SRI is defence-in-depth.
- Generalise the srcDoc host into the reusable runtime described in the framework
  initiative.

## Migration notes

`0017_questionsubpart_interactive_html_and_more` — two nullable/defaulted fields;
non-breaking. Re-import (or a future widget author) populates them.
