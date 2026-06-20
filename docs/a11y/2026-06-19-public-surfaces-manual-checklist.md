# Manual a11y checklist — public surfaces (2026-06-19, A11Y-5)

Companion to the automated axe gate (`e2e/a11y.spec.ts`) and the static
`eslint-plugin-jsx-a11y` lint gate. axe catches ~30–40% of WCAG issues; this
checklist covers the keyboard + screen-reader behaviours a static/automated scan
cannot. Re-run it when the public surfaces change materially.

**Scope:** `/`, `/login`, `/register`, `/register/school`, `/register/open`,
`/enquire`.

## Keyboard-only walkthrough (no mouse)

For each route, unplug the mouse / use Tab, Shift+Tab, Enter, Space, Esc only:

- [ ] **Skip link** appears on first Tab and jumps to `#main-content`.
- [ ] **Tab order** follows visual/reading order; no off-screen or trapped focus.
- [ ] **Focus is always visible** (`focus-visible` ring) on every interactive
      element — links, inputs, selects, buttons, the language switcher.
- [ ] **All controls operable by keyboard**: text inputs typeable; selects
      openable with Enter/Space + arrow keys; buttons fire on Enter/Space.
- [ ] **Forms submit** with Enter from a focused field; the primary CTA is
      reachable and activates.
- [ ] **No keyboard trap** — focus can always leave any control/region.
- [ ] **Language switcher (EN/हिं/मरा)** is reachable and operable; switching
      keeps focus sensible.

## Screen-reader spot-check (NVDA on Windows / VoiceOver on macOS)

- [ ] **Page has one `h1`** announced; heading levels don't skip (h1 → h2 → h3).
- [ ] **Landmarks** announced: a single `main`; banner/contentinfo where present.
- [ ] **Every form field** announces an accessible **name** (its label) and its
      type; required/error states are announced.
- [ ] **Buttons/links** announce meaningful names (not "button"/"link" alone or
      raw icon markup).
- [ ] **Errors** (e.g. failed login) are announced, not only shown visually.
- [ ] **Images/logos** have appropriate alt text or are correctly decorative.

## Known issues (tracked, not regressions)

- **Brand-button contrast** — `.btn-brand` (white on `#FF6F00`, ≈ 2.8 : 1) fails
  WCAG AA in its enabled state across the app. Deferred to **A11Y-4** pending a
  brand-shade design decision (see `docs/changes/2026-06-19-a11y-batch1.md`). This
  is why `/` (enabled hero CTA) stays axe **reporting-mode** rather than gated.
- **`/design`** intentionally renders low-contrast swatches, non-unique iframe
  titles, and unlabeled widget range inputs as showcase examples — reporting-mode
  by design.
