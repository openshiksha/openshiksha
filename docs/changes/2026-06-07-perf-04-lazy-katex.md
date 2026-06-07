# PERF-04 — Lazy-load KaTeX behind the math renderer

**Date:** 2026-06-07
**Initiative:** Performance Budget
**Classification:** Improve

## Summary

Moves the 257 kB / 77 kB-gzip `vendor-katex` chunk off the first-paint critical
path. `<RichContent>` now dynamic-imports KaTeX (and its CSS) **only** when the
text it's about to render actually contains math delimiters (`$…$`, `\(…\)`,
`$$…$$`, `\[…\]`, `\begin{…}`). Non-math routes — dashboards, browse pages,
profile, settings, the parent landing page — never trigger the load.

## Design

`renderRichContent.ts`:
- Replaced the static `import katex from 'katex'` with a module-level reference
  `katexRef` plus exported `setKatex(mod)` / `isKatexLoaded()` helpers.
- Added `textContainsMath(text)` (cheap regex pre-check).
- `renderKatex()` falls back to an escaped `katex-pending` inline-code span when
  `katexRef` is null. The component re-renders to swap in real KaTeX output
  once the chunk loads.

`RichContent.tsx`:
- Uses a single module-level `loadKatex()` that returns a memoised
  `Promise.all([import('katex'), import('katex/dist/katex.min.css')])` so all
  in-flight `<RichContent>` instances share one network fetch.
- `useEffect` only kicks off the load when the text contains math AND KaTeX
  isn't already loaded.
- `katexReady` participates in the `useMemo` dependency key (eslint-suppressed
  with rationale) so the renderer re-runs once KaTeX arrives.

`test-setup.ts`:
- Preloads KaTeX synchronously via static import + `setKatex(katex)` so the
  existing sync renderer tests don't have to become async.

## Verification

- `npm run type-check` — green.
- `npm run lint` — green (`--max-warnings 0`).
- `npm test -- --run` — 31 files / 194 tests pass.
- `npm run build` — green; `dist/index.html` lists only
  `vendor-react`, `vendor-query`, `vendor-dompurify`, and `rolldown-runtime`
  as `modulepreload`. **`vendor-katex` is no longer preloaded** — it's fetched
  on demand by the math renderer.
- Manual sanity: a math-containing `<RichContent>` still resolves to KaTeX
  output (the existing 19 renderer tests cover this with the pre-loaded module).

## Entry-chunk progress

| Stage                                          | Entry JS  | Gzip      |
| ---------------------------------------------- | --------- | --------- |
| Baseline                                       | 855 kB    | 247 kB    |
| Post-PERF-01 (vendor split)                    | 353 kB    |  92 kB    |
| Post-PERF-03 (route lazy)                      | 131 kB    |  41 kB    |
| **Post-PERF-04 (KaTeX off the critical path)** | **132 kB** | **41 kB** |

Entry-chunk size is unchanged from PERF-03 (KaTeX was already in its own
`vendor-katex` chunk), but the *first-paint preload set* drops by ~77 kB gzip
— that's the win this PR delivers.

## Next steps

PERF-06 (CI bundle-size budget guard) locks the post-cut entry-chunk size in.
