# Manual a11y checklist — student core loop (2026-06-23, A11Y-8)

Companion to the automated axe gate (`e2e/a11y.spec.ts`, the four `auth: true`
student routes) and the static `eslint-plugin-jsx-a11y` lint gate. axe catches
~30–40% of WCAG issues; this checklist covers the keyboard + screen-reader
behaviours a static/automated scan cannot. Re-run it when the student core loop
changes materially. Mirrors the Batch-1 public-surfaces checklist.

**Scope:** `/student` (dashboard), `/student/assignments/:id` (assignment detail
+ answer form + submit), `/student/proficiency`, `/student/srs-drill/:entryId`.

## Keyboard-only walkthrough (no mouse)

Tab / Shift+Tab / Enter / Space / Esc / arrow keys only, across the full loop
(dashboard → open an assignment → answer → submit → proficiency → drill):

- [ ] **Skip link** appears on first Tab and jumps to `#main-content`.
- [ ] **Tab order** follows visual/reading order; no off-screen or trapped focus.
- [ ] **Focus is always visible** (`focus-visible` ring, A11Y-FV) on every
      interactive element — nav/tab bar, assignment cards, answer controls,
      Save/Submit buttons, the language switcher.
- [ ] **Answer controls operable by keyboard**: MCQ radios selectable with arrow
      keys within the group; numeric/fill-blank inputs typeable; the auto-save
      textarea editable; Submit fires on Enter/Space.
- [ ] **Bottom tab bar / account drawer** (mobile chrome) reachable and operable;
      drawer closes on Esc and returns focus sensibly.
- [ ] **No keyboard trap** — focus can always leave any control/region, including
      any dialog/side-sheet.
- [ ] **Drill flow** (`/student/srs-drill`) fully operable: answer → reveal →
      next, all by keyboard.

## Screen-reader spot-check (NVDA on Windows / VoiceOver on macOS)

- [ ] **Page has one `h1`** announced; heading levels don't skip (h1 → h2 → h3).
- [ ] **Landmarks** announced: a single `main`; nav/banner/contentinfo where
      present.
- [ ] **Every answer field** announces an accessible **name** (its label) and its
      type; the radio group announces its question (subpart) as the group label.
- [ ] **Save/Submit/Next buttons** announce meaningful names (not "button" alone).
- [ ] **Score / feedback** after submit is announced, not only shown visually.
- [ ] **Proficiency sparklines** are announced with a summarizing `aria-label`
      (decorative-data SVGs, `role="img"`), not read as raw paths.

## Known issues (tracked, not regressions)

- **Residual `color-contrast` in axe `incomplete`** — a handful of nodes whose
  background axe cannot compute land in the `incomplete` bucket (recorded in
  `axe-report/student-*.json`), not the blocking set. These are not AA failures of
  the V2 token palette; the gate asserts only `blocking === []`. Same contract as
  the gated public routes.
