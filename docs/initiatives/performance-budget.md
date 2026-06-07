# Performance Budget — Initiative

> **North Star:** A K-12 student on a slow Indian mobile network gets a fast
> first paint. The initial JS payload is **route-split and under a hard,
> CI-enforced budget**; heavy libraries (KaTeX, charts) load only on the
> routes that need them; the build never silently regresses past the budget
> again.
>
> **Status:** 🟢 **Active** (promoted 2026-06-07). Top priority now that V2,
> Cabinet Data Fidelity, and Legacy Parity are closed and Interactive Widgets
> is paused after IW-8.

**Last updated:** 2026-06-07

---

## A. Why this initiative exists

The Vite build prints a standing warning:

```
dist/assets/index-*.js  770 kB
```

Every page of the app is **statically imported** in
[`src/App.tsx`](../../frontend_modern/src/App.tsx) — all ~30 route components
(student, teacher, parent, admin, the dev-only `/design` and `/widgets/dev`
pages) plus heavy libraries (KaTeX math rendering) are pulled into **one
monolithic chunk**. A student opening the login page downloads the entire
teacher authoring surface, the admin classroom manager, the widget dev
playground, and the math engine before they can type a password.

On a K-12 mobile network (the actual target audience — Indian students on
2G/3G/budget Android), a 770 kB JS bundle is **seconds** of blank screen.
This is the single biggest unaddressed quality gap on the migrated surfaces:
the app is feature-complete but not yet *fast*.

This initiative makes the app fast **and keeps it fast** — the second half
matters as much as the first. Without a CI budget guard, a future PR
re-bloats the bundle and nobody notices until a student does.

There is also low-hanging dead weight: `recharts` (a heavy charting library)
is in `package.json` but **imported nowhere** — the proficiency sparklines are
hand-rolled SVG. It should go.

---

## B. Design principles

1. **Measure first, then cut.** Land the measurement harness (bundle
   visualizer + recorded baseline) before changing app code, so every
   subsequent PR can show its delta.
2. **Eager only what the first paint needs.** Auth + marketing home render
   for unauthenticated visitors — keep them eager. Everything behind
   `ProtectedRoute` (dashboards, authoring, admin, dev tools) is lazy.
3. **Heavy libraries load on demand.** KaTeX loads with the routes that
   render math, not on app boot. Charting libs, if reintroduced, are always
   in their own chunk.
4. **Split, don't rewrite.** Code-splitting is a wrapping/config change, not
   a refactor of feature logic. Each PR stays atomic and reversible.
5. **Lock in the win.** A CI bundle-size budget fails the build if the
   initial chunk exceeds the agreed ceiling. Wins are defended, not just won.
6. **No UX regression.** A `<Suspense>` fallback uses the existing
   `LoadingSpinner`; lazy boundaries never flash a blank screen or break the
   existing route guards / tests.

---

## C. Backlog — PERF-01 → PERF-06 (each ≈ one reviewable PR)

Built **lowest-risk-first**. PERF-01 and PERF-02 are independent and pure
config/dependency changes. PERF-03 is the big win. PERF-06 (the CI guard)
lands last so it locks in the budget *after* the cuts.

### PERF-01 — Measurement harness + vendor `manualChunks` *(do first; foundation)*
Pure `vite.config.ts` change — no app code touched.

- Add `rollup-plugin-visualizer` as a devDependency and a
  `npm run build:analyze` script that emits `dist/stats.html`.
- Add `build.rollupOptions.output.manualChunks` to split the obvious vendor
  groups into their own files: `react`/`react-dom`/`react-router-dom`,
  `@tanstack/react-query`, `katex`, `dompurify`. Vendor code changes rarely,
  so splitting it improves caching even before route-splitting lands.
- Set `build.chunkSizeWarningLimit` honestly (don't hide the warning — record
  the real number).
- Record the **baseline** (per-chunk sizes, gzip) in
  `docs/perf/baseline-2026-06-07.md`.
- **Verify:** `npm run build` succeeds; `dist/` now contains separate vendor
  chunks; baseline doc committed.

### PERF-02 — Remove unused `recharts` dependency
`recharts` (`^3.8.1`) is imported nowhere in `src/` (proficiency charts are
hand-rolled SVG). Drop it from `package.json`.

- **Verify:** `grep -rn "recharts" frontend_modern/src` is empty;
  `npm install` + `npm run build` + `npm test` green; node_modules shrinks.

### PERF-03 — Route-level code-splitting with `React.lazy` *(the big win)*
Convert the route component imports in `App.tsx` to `React.lazy` and wrap the
`<Routes>` tree in a single `<Suspense fallback={<LoadingSpinner />}>`.

- **Keep eager** (first-paint critical): `LoginPage`, `RegisterPage`,
  `HomePage`, `AppShell`, `ProtectedRoute`, `LoadingSpinner`, `ErrorBoundary`,
  `NotFoundPage`.
- **Make lazy:** every authenticated/teacher/parent/admin page, plus the
  dev-only `DesignSystemPage` and `WidgetDevPage` (these should *never* be in
  a student's first load).
- Lazy modules need a default-or-named export shim — most feature pages are
  named exports, so use the `lazy(() => import('...').then(m => ({ default: m.X })))`
  pattern.
- **Verify:** `npm run build` shows the main chunk shrink dramatically and
  many small per-route chunks appear; `npm test` green (Suspense resolves in
  tests); Playwright smoke nav still passes; record the new sizes vs. the
  PERF-01 baseline in the change doc.
- **What could go wrong:** a named-export miss → blank route; a missing
  Suspense boundary → React throws. Mitigate by one shared top-level
  `<Suspense>` and a per-route render check.

### PERF-04 — Lazy-load KaTeX behind the math renderer
KaTeX is only needed where questions render. With PERF-03 it already moves
into the chunks that import `RichContent`, but the **font CSS + core** can be
deferred further so non-math routes never pay for it.

- Make [`renderRichContent.ts`](../../frontend_modern/src/shared/ui/renderRichContent.ts)
  load the KaTeX module via a dynamic `import()` on first math render (cache
  the promise), or split `RichContent` into a `React.lazy` boundary so KaTeX
  is fetched only when a question/preview mounts.
- **Verify:** a route with no math (dashboard) no longer pulls the KaTeX
  chunk on first load (check `dist/stats.html`); math still renders correctly
  on `AssignmentDetailPage` + `CreateQuestionPage` preview; tests green.
- **What could go wrong:** async load means a one-frame unstyled flash —
  render a plain-text fallback until KaTeX resolves.

### PERF-05 — Font loading optimization
The Google Fonts `<link>` in `index.html` requests the full Inter + Fraunces
weight/optical-size ranges. Trim to the weights actually used and confirm
`display=swap` + `preconnect` are optimal; consider self-hosting the two
families as a follow-up (woff2, `font-display: swap`) to drop a render-blocking
third-party round trip.

- **Verify:** Lighthouse/network panel shows fewer font bytes and no
  render-blocking on first paint; the V2 type system is visually unchanged
  (Fraunces display + Inter body).
- **Independent** of PERF-01..04; can ship any time.

### PERF-06 — CI bundle-size budget guard *(lands last; locks in the win)*
A CI step that **fails the build** if the initial (entry) chunk exceeds an
agreed ceiling (set just above the post-PERF-03 measured size, e.g. round
number with headroom).

- Add a small Node script (`scripts/check-bundle-budget.mjs`) run after
  `npm run build` in the frontend CI job; it reads the built entry chunk size
  and exits non-zero past the budget, printing the offending chunk.
- Wire it into the existing GitHub Actions frontend job.
- Document the budget + how to raise it deliberately in
  `docs/perf/budget.md`.
- **Verify:** the guard passes on the current (post-cut) build and fails a
  deliberately-bloated test build.

**Suggested order:** PERF-01 → (PERF-02 ∥ PERF-05) → PERF-03 → PERF-04 →
PERF-06. PERF-02 and PERF-05 are independent quick wins that can land in any
order; PERF-06 must come after PERF-03 so the budget reflects the cut.

---

## D. Continuous Improvement list (the compounding step)

Pick one small hardening task whenever advancing this initiative:

- Add a per-route chunk to the bundle-stats doc so regressions are diffable.
- Convert one more eager import to lazy where first-paint doesn't need it.
- Add a `prefers-reduced-data` or low-bandwidth hint somewhere it helps.
- Preload the next-likely route's chunk on hover/idle (`<link rel=modulepreload>`).
- Tighten the CI budget ceiling by the realized headroom.
- Tree-shake or replace one more heavy dependency.

---

## E. Definition of Done (North Star reached)

- The Vite build no longer prints a single oversized-chunk warning; the entry
  chunk is route-split and well under the budget.
- Auth/home first paint downloads only what an unauthenticated visitor needs;
  teacher/admin/dev surfaces and KaTeX load on demand.
- A CI budget guard fails any PR that pushes the entry chunk past the ceiling.
- `recharts` and any other unused heavy deps are gone.
- No UX or test regression: route guards, Suspense fallbacks, and Playwright
  smoke navigation all pass.

---

## F. Relationship to other initiatives

- **V2 "Chalk & Unlock"** owns the visual language — font optimization
  (PERF-05) must not change the Fraunces+Inter type system, only how it loads.
- **Interactive Widgets** runtime is sandboxed in an iframe (`srcdoc`), so the
  widget runtime bundle is already isolated from the main chunk — this
  initiative leaves that boundary intact and benefits from route-splitting the
  *host* pages.
- **Accessibility pass** (backlog) — Suspense fallbacks added here must keep
  the existing a11y baseline (focus management on route change).

---

## G. Progress Ledger

| Date | Increment | PR | Hardening / learning |
|---|---|---|---|
| 2026-06-07 | Initiative promoted ⚪ Proposed → 🟢 Active; PERF-01…PERF-06 backlog written. | _(this docs PR)_ | Promoted because all prior top initiatives are closed/paused and the 770 kB single-chunk warning is the biggest standing quality gap for the K-12 mobile audience. |
