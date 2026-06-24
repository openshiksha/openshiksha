# Manual a11y checklist — teacher & parent surfaces (2026-06-23, A11Y-12)

Companion to the automated axe gate (`e2e/a11y.spec.ts`, the `auth: 'teacher'` /
`auth: 'parent'` routes) and the static `eslint-plugin-jsx-a11y` lint gate. axe
catches ~30–40% of WCAG issues; this checklist covers the keyboard +
screen-reader behaviours a static/automated scan cannot. Re-run it when these
surfaces change materially. Mirrors the Batch-1/Batch-2 checklists.

**Scope (gated):** `/teacher` (dashboard), `/teacher/questions` (question bank),
`/teacher/grading` (AI grading queue), `/parent` (dashboard).
**Not yet gated (noted):** the dense authoring forms (`/teacher/questions/new`,
`/teacher/assignments/new`, `/teacher/problem-sets/new`) and parent insights
(`/parent/insights`, `/parent/insights/:childId`) — a future increment.

## Keyboard-only walkthrough (no mouse)

Tab / Shift+Tab / Enter / Space / Esc / arrow keys only:

- [ ] **Skip link** appears on first Tab and jumps to `#main-content`.
- [ ] **Tab order** follows visual/reading order; no off-screen or trapped focus.
- [ ] **Focus is always visible** (`focus-visible` ring, A11Y-FV) on every
      interactive element — nav/tab bar, dashboard cards, question-bank
      search/filter controls, grading-queue actions, parent tab switcher + the
      "View insights" link.
- [ ] **Controls operable by keyboard**: search inputs typeable; filter selects
      openable with Enter/Space + arrows; card/link CTAs fire on Enter/Space;
      parent progress/assignments tabs switch with the keyboard.
- [ ] **Bottom tab bar / account drawer** (mobile chrome) reachable; drawer closes
      on Esc and returns focus sensibly.
- [ ] **No keyboard trap** — focus can always leave any control/region, including
      any dialog/side-sheet (e.g. the question-bank detail sheet).

## Screen-reader spot-check (NVDA on Windows / VoiceOver on macOS)

- [ ] **Page has one `h1`** announced (rendered via `SectionHeading as="h1"`);
      heading levels don't skip.
- [ ] **Landmarks** announced: a single `main`; nav/banner/contentinfo where
      present.
- [ ] **Search / filter fields** announce an accessible name and type.
- [ ] **Buttons / links** announce meaningful names (not "button"/"link" alone or
      raw icon markup) — dashboard CTAs, grading actions, "View insights".
- [ ] **Empty states** (no rooms / no questions / no children) announce their
      heading + message, not a bare blank region.

## Known issues (tracked, not regressions)

- **Authoring forms not yet gated** — `CreateQuestionPage` / `CreateAssignmentPage`
  / `CreateProblemSetPage` carry richer form interactions likely to need a
  dedicated label/landmark pass; deferred to a future Batch-3 increment, kept in
  reporting-mode until measured + remediated (never gate a dirty route).
- **Residual `color-contrast` in axe `incomplete`** — nodes whose background axe
  can't compute land in the non-gating `incomplete` bucket (recorded in
  `axe-report/{teacher,parent}-*.json`); the gate asserts only `blocking === []`.
