# 2026-06-20 — A11Y-4: Brand-shade decision + contrast token sweep + gate `/`

## Summary
Resolves the one systemic colour-contrast finding deferred from Accessibility
Batch 1: white text on `.btn-brand` (`#FF6F00`, ≈ 2.8 : 1) failed WCAG 2.1 AA.
Makes the brand-shade decision concretely, sweeps small brand-text usages to the
on-text shade, documents the rule, and flips the home route (`/`) to a gated axe
surface now that its enabled hero CTA passes.

## Classification
**Improve** — extends the V2 token system with a documented, enforced contrast
rule. Frontend-only; no API or schema change.

## The decision
- `brand-600` (`#FF6F00`) is preserved as the **decorative / large-element
  anchor** (logo, chalk-underline, large display numerals, borders, focus rings,
  icon glyphs, big badges) — WCAG only needs 3 : 1 (large/non-text) or nothing
  (decoration) there, so the vivid brand identity is untouched.
- `brand-700` is retuned from `#CC5800` (≈ 4.2 : 1, short of AA) to **`#C05300`
  (≈ 4.7 : 1 white)** — the on-text / CTA brand shade. `brand-800 #9E4500`
  (≈ 6.1 : 1) stays the hover target.

## What changed
- `tailwind.config.js`: `brand-700` `#CC5800` → `#C05300`.
- `src/index.css`: `.btn-brand` fill `bg-brand-600` → `bg-brand-700`, hover
  `brand-700` → `brand-800`; `.prose-osh a` `text-brand-600` → `text-brand-700`
  (hover `brand-800`).
- Swept small brand text (uppercase kickers, text links ≤ `text-sm`) from
  `text-brand-600` → `text-brand-700` across `HomePage`, `SectionHeading`,
  `DesignSystemPage`, `CreateAssignmentPage`, `CreateProblemSetPage`,
  `CreateQuestionPage`, `QuestionBankPage`, `QuestionPreviewPanel`,
  `WidgetGalleryPanel`, `WidgetDevPage`. Left `text-brand-600` on large display
  text (`NotFoundPage` 404), decorative SVG icon glyphs, and native form-control
  accent colours (checkbox/radio `text-brand-600`, a UI-component boundary).
- `e2e/a11y.spec.ts`: flipped `home` (`/`) to `gate: true`.
- `docs/initiatives/2026-design-system-v2.md`: documented the Contrast rules +
  retuned the colour-token table.

## Legacy reference
None — legacy Django 1.11 had no contrast/accessibility story. Net-new.

## Tests
- `npm run type-check`, `npm run lint` (`--max-warnings 0`), `npm run build` — green.
- `npx vitest run` — 77 files / 467 tests pass.
- Contrast verified by relative-luminance math: white on `#C05300` ≈ 4.69 : 1 (AA pass).
- The axe gate on `/` runs in CI `frontend-e2e` (Playwright).

## Next steps
A11Y-FV (focus-visible audit), then the authenticated axe harness (A11Y-6) +
student core-loop remediation/gating (A11Y-7/8).
