# `shared/ui` — V2 design-system primitives

The reusable building blocks of the **"Chalk & Unlock"** design language. Build
new screens from these, not from raw Tailwind. Full plan:
[`docs/initiatives/2026-design-system-v2.md`](../../../../docs/initiatives/2026-design-system-v2.md).

## Conventions (follow these so multi-session work stays coherent)

1. **Tokens only — never raw hex.** Use `brand-*`, `ink-*`, semantic
   (`emerald/amber/rose`) tokens and the `.os-card` / `.btn-brand` / `.input-brand`
   classes. If a shade is missing, add it to `tailwind.config.js` and note it in
   the initiative ledger — don't inline a colour.
2. **No legacy palette in new code.** Don't use `primary` (blue), `indigo`, or
   cold `gray-50/100` backgrounds. They exist only so un-migrated pages render.
3. **Headings use `font-display` (Fraunces); body/UI uses `font-sans` (Inter).**
4. **Accessible by default.** Real labels, `:focus-visible` (global ring is
   provided), AA contrast, `prefers-reduced-motion` honoured (handled globally in
   `index.css`).
5. **Compose, don't fork.** Extend a primitive's props before creating a near-
   duplicate. Two cards that differ by one prop should be one component.
6. **Every new primitive is exported from `index.ts` AND rendered in
   `features/design/DesignSystemPage.tsx`.** The `/design` route is the living
   catalogue; if it isn't there, it doesn't exist.

## Current primitives

| Component | Purpose |
|---|---|
| `Logo` | Brand mark / wordmark (`variant`, `size`, `float`, `wordmarkClassName`). |
| `Button` | Actions — `variant: 'brand' \| 'ghost'`, `size: 'sm' \| 'md' \| 'lg'`. |
| `Card` | The warm `.os-card` surface (`padded`). |
| `Badge` | Status pill — `tone: 'brand' \| 'neutral' \| 'success' \| 'attention' \| 'urgent'`. |
| `RichContent` | Sanitised HTML + KaTeX renderer (`text`, `variant`). Use for any question/option/solution/hint content from the API. |
| `Skeleton` | Branded loading placeholder (`w`, `h`, `rounded`). Warm `ink-100` pulse. |

## Wanted next (see backlog `M1-06`)

`Input`, `Stat`, `SectionHeading`, `EmptyState` (keyhole motif),
`ProgressRing` ("unlock" mastery).

## Adding a component

1. Create `MyThing.tsx` here — tokens only, accessible, documented props.
2. Export it from `index.ts`.
3. Render it (all meaningful states) in `DesignSystemPage.tsx`.
4. `npm run type-check && npm run lint && npm run build` green.
5. Update the initiative's Progress Ledger.
