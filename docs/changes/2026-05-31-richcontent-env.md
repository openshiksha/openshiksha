# 2026-05-31 — RichContent un-delimited environment detection (M7-04)

## Summary

Teach the shared `<RichContent />` primitive to recognise un-delimited LaTeX
environments (`\begin{X}…\end{X}`) as block math and route them through KaTeX
in `displayMode`. Without this, Cabinet content that uses raw `\begin{array}`
tables (the entire Q3 salary-table family from the 2026-05-30 visual audit)
rendered as literal `\begin{array}{c|lcr}` text on the page.

## Classification

Improve — extends M7-01 (`RichContent`, PR #114) and stays inside the same
sanitise → KaTeX pipeline.

## Files touched

- `frontend_modern/src/shared/ui/renderRichContent.ts` — add `ENV_RE` first in
  the delimiter table with `exprGroup: 0` (feed the whole match, `\begin` and
  `\end` included, to KaTeX).
- `frontend_modern/src/shared/ui/RichContent.test.tsx` — five new tests:
  `\begin{array}` typesets as block math, env wins over inner `$`-style
  delimiters, truncated `\begin{` doesn't crash, `<div>…\(…\)…</div>` nested
  case, `<table>` + inline KaTeX render side-by-side.

## What changed and why

- The renderer previously only matched the four `$`/`\(`/`$$`/`\[` delimiter
  pairs. Cabinet content for tables and aligned equations ships the bare
  `\begin{array}` form (no surrounding `$$`), so those regions emerged on the
  page as raw LaTeX source.
- The new regex is `/\\begin\{([a-zA-Z*]+)\}[\s\S]*?\\end\{\1\}/g`: non-greedy,
  with a back-reference to the opening env name. Cabinet envs don't nest, so
  this is safe across the 644-question corpus. Truncated openers are simply
  unmatched and pass through as escaped text — no crash.
- The env rule is listed **first** in `DELIMITERS` so its hits are added to the
  `findMath()` array before `$…$` etc. The existing cursor-based merge then
  skips overlapping inner `$` matches automatically.
- `exprGroup: 0` is new: env hits feed the *entire* match (begin + body + end)
  to KaTeX; the existing `$…$` family keep `exprGroup: 1` so they strip the
  delimiters.

## Tests

`npm test src/shared/ui/RichContent.test.tsx` — 17 passing (12 prior + 5 new).
`npm run type-check`, `npm run lint`, `npm run build` all clean.

## Skeleton (M1-06 carry-over)

`shared/ui/Skeleton.tsx` and its `index.ts` export are already on
`modernization` (landed alongside M7-01). No code change required; consumers
will adopt as new loading surfaces appear in the V2 dashboards.

## Next steps

- M7-09 `infer_taxonomy_names` management command (next PR in this batch).
- M7-07 shared stem field + importer lift.
- M7-05 tag-collision fix.
- M7-03 per-subpart type + grader dispatch.
