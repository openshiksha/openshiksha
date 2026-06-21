# 2026-06-20 — A11Y-FV: Robust keyboard focus-visible indicator

## Summary
Hardens the global `:focus-visible` indicator so every focusable control shows a
reliable, AA-compliant focus ring for keyboard users (WCAG 2.4.7 Focus Visible,
2.1.1 Keyboard, 1.4.11 Non-text Contrast).

## Classification
**Improve** — frontend-only, single CSS rule. No API or component changes.

## The problem with the old ring
The previous indicator was a `box-shadow` ring
(`box-shadow: 0 0 0 2px #fffaf3, 0 0 0 4px rgba(255,111,0,0.55)`). Two defects:

1. **Suppressed on key primitives.** `.btn-brand` sets its own `box-shadow`
   (`shadow-soft`) in the `components` cascade layer, which **wins over** the
   base-layer `:focus-visible` box-shadow — so the primary CTA showed *no* focus
   ring when tabbed to.
2. **Clipped by ancestors.** A box-shadow ring is clipped by any
   `overflow:hidden` ancestor (common in cards/menus), so the ring vanished in
   many contexts.
3. **Contrast.** The orange ring at 55% opacity was well under the 3:1 Non-text
   Contrast bar against paper.

## The fix
Switch to a real `outline` (painted by the UA on top of everything, never
suppressed by element box-shadows, never clipped by `overflow`):

- `:focus-visible { outline: 2px solid #c05300; outline-offset: 2px; }` —
  `brand-700` (#C05300) clears ≥ 3:1 on paper (the brand anchor #FF6F00 is only
  ≈ 2.8:1 and would fail).
- `.btn-brand:focus-visible { outline-color: #1a1816; }` — on the solid-orange
  CTA a dark ink ring frames the button far more legibly (≈ 16:1 on paper).

## Legacy reference
None — legacy had no keyboard-focus story. Net-new.

## Tests / how to verify
- `npm run build` + `npm run lint` (`--max-warnings 0`) — green.
- Manual: Tab through `/login`, `/student`, an assignment — every stop shows a
  visible ring incl. `.btn-brand`; mouse clicks show no ring (`:focus-visible`).
- Respects the existing `prefers-reduced-motion` block (unchanged).

## Next steps
Authenticated axe harness (A11Y-6) + student core-loop remediation/gating
(A11Y-7/8). Captured in the A11Y-8 manual keyboard checklist.
