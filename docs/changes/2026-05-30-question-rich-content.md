# 2026-05-30 — Question content rendering (HTML + LaTeX)

**Initiative:** [V2 "Chalk & Unlock" design overhaul](../initiatives/2026-design-system-v2.md) · **Increment:** `M7-01` (+ `M1-06` partial — `Skeleton` primitive)
**Classification:** Improve

## Summary

Questions, MCQ options, hints, and worked solutions are now rendered as
sanitised HTML with KaTeX-typeset math instead of printed as raw markup. The
work introduces a new shared design-system primitive — `<RichContent />` — and
wires it into every question surface (`QuestionCard`, the SRS drill via
`QuestionCard`, and the teacher `CreateQuestionPage` live preview). A second
primitive, `<Skeleton />`, lands alongside it and replaces the indigo spinner
on the SRS drill's loading state.

## Legacy reference

- Legacy `sphinx/templates/` server-rendered question HTML and let MathJax
  typeset math in the browser. Cabinet ships question content with
  `\(...\)` / `\over` / `\sqrt` and HTML wrappers (`<p>`, `<sup>`, `<sub>`,
  `<img>`).
- Modern `QuestionCard` previously only handled `$…$` / `$$…$$` and printed
  HTML tags as visible text — discovered while reviewing the V2 shell as
  `student_demo` (`docs/initiatives/screenshots/questions-broken-before.png`).

## What changed

### New `shared/ui/` primitives
- `shared/ui/renderRichContent.ts` — pure renderer: DOMPurify sanitisation
  (allowlist of inline/block tags, `<img>`, `<table>`; strips `script`,
  event handlers, `javascript:` URLs) then a `TreeWalker` over text nodes
  replacing each LaTeX run with `katex.renderToString` output. Delimiters
  supported: `$…$`, `\(…\)` (inline) and `$$…$$`, `\[…\]` (block).
- `shared/ui/RichContent.tsx` — memoised component wrapper, exposes
  `text`, `variant: 'block' | 'inline'`, `className`. Wraps the output in
  `<div class="prose-osh">` for warm `ink` body text and brand links.
- `shared/ui/Skeleton.tsx` — branded loading placeholder with `w`, `h`,
  `rounded` Tailwind-utility props; warm `ink-100` pulse; `role="status"`
  for screen readers.
- `shared/ui/index.ts` exports both. `shared/ui/README.md` updated.
- `src/index.css` gains a `prose-osh` component class — warm body, brand
  links, list/table/img defaults, `.katex-display` spacing.

### Wired into the product
- `features/student/QuestionCard.tsx` — local `renderMixedContent` deleted;
  `RichContent` now renders subpart question text (block), MCQ/multi-select
  option text (inline), hint text (inline), and worked solutions (block,
  inside the existing `CollapsibleReveal`).
- `features/teacher/CreateQuestionPage.tsx` — local KaTeX-only `renderPreview`
  collapsed to a one-liner that delegates to `<RichContent />`, so authors
  see exactly what students will see.
- `features/student/SRSDrillPage.tsx` — replaces the indigo spinner with a
  branded `Skeleton` block (drill questions are rendered by `QuestionCard`,
  so the LaTeX/HTML fix automatically applies to the SRS surface).
- `features/design/DesignSystemPage.tsx` — adds **Rich content (HTML + LaTeX)**
  and **Skeleton** sections so the primitives are visible in the living
  catalogue.

### Dependencies
- Added `dompurify@^3.4.7` (runtime) and `@types/dompurify@^3.0.5` (dev).
  Small, zero transitive risk; sanitisation now decoupled from KaTeX.

## Tests

`frontend_modern/src/shared/ui/RichContent.test.tsx` (Vitest + happy-dom) —
12 tests covering:
- empty input → empty output;
- KaTeX rendering for each delimiter set (`$…$`, `\(…\)`, `$$…$$`, `\[…\]`);
- block vs inline detection (`katex-display` only on block);
- `<script>` tags stripped; `javascript:` URLs stripped from `<img src=…>`;
- allowlisted tags preserved (`strong`, `em`, `sup`/`sub`, `ul/li`, `img`, `table`);
- LaTeX inside an HTML wrapper still renders;
- Cabinet-style fragment with multiple inline math spans renders all of them.

Plus a smoke test on `<RichContent />` itself (renders nothing for empty
text; emits `.prose-osh` + `.katex` for real content; no `<script>` survives).

Run: `npm test -- --run` → **6 test files, 33 tests pass.**
`npm run type-check`, `npm run lint`, `npm run build` all green.

## How to verify

1. `cd frontend_modern && npm test -- --run && npm run build`.
2. `docker compose up -d --build postgres backend frontend`,
   `docker compose exec backend python manage.py migrate && … seed_demo_data`.
3. Log in as `student_demo` / `demo1234`, open the imported assignment, and
   confirm question text + MCQ options + worked solutions render with typeset
   math and no visible `\(`, `\)`, `\over`, or `<p>` tags. Capture screenshot
   to `docs/initiatives/screenshots/questions-fixed-after.png`.
4. `/design` shows the new "Rich content" + "Skeleton" sections.

## Migration notes

None. Pure frontend; no schema, no API, no env-var changes.

## Next steps

- `M7-02` — variable substitution (`{4*j}` widgets). Decide
  backend-realised vs. frontend-evaluated; port legacy croupier widget types.
- `M7-03` — wire Browse / Question Bank / assignment-list filters and search.
- `M4-01` — Student Dashboard in V2 language (highest-traffic surface).
