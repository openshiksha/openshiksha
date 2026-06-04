# 2026-06-03 — Profile/Settings page migrated to V2 design system

## Summary
Migrated `features/shared/ProfilePage.tsx` from the legacy
`indigo`/cold-gray template to V2 "Chalk & Unlock" tokens + `src/shared/ui`
primitives. Smallest M4 surface, picked first in the day's batch as the
lowest-risk pass.

## Classification
Improve — no behavioral change; reskin only.

## Legacy files referenced
None (frontend reskin; no legacy Django template to honour for the profile form).

## What changed
- Replaced the local `FormField` helper with `<Input>` from `@/shared/ui`.
- Wrapped the form in `<Card>` (`.os-card` warm paper surface).
- Title uses `<SectionHeading as="h1">` (`font-display`).
- Save button now uses `<Button variant="brand">`.
- All `indigo-*` / `text-gray-*` / `border-gray-*` classes swapped for the
  V2 token palette (`brand-*`, `ink-*`, `rose-*`, `emerald-*`).
- Avatar circle uses `brand-100`/`brand-700` instead of `indigo-100`/`indigo-700`.
- Checkbox accent recoloured to `brand-600`/`brand-500`.

## Tests
- `npm run type-check` — green
- `npm run lint` — green
- `npm test -- --run` — 84/84 green (no test for ProfilePage changed)
- `npm run build` — green

## Verification
Grep over the migrated file for legacy tokens returns zero hits:
`primary`, `indigo`, `blue-`, `bg-gray-50`, `text-gray-`.

## Next
PRs 2–5 in today's batch will migrate Parent, Admin, Proficiency-cluster, and
Assignment/SRS surfaces to V2.
