# M3-03 — Public Enquire page → V2

**Classification:** Improve.

## Summary
The public `/enquire` page (prospective schools) was the last un-migrated
authenticated/unauthenticated surface — it wore the legacy
`bg-gradient-to-br from-indigo-50 to-blue-100` template + a fake "OS" tile.
Migrate it to the V2 chalkboard/paper `AuthLayout` shared with Login and
Register, and rebuild the form on `ui/Input` + `ui/Textarea` + `ui/Button`.

## Files changed
- `frontend_modern/src/features/enquiry/EnquirePage.tsx`

## What changed
- Wrapped in `<AuthLayout>` — chalkboard hero on the left, warm paper form
  panel on the right; mobile fallback compact-brand. Now every external-
  facing surface (Login, Register, Register-school, Register-open, Enquire)
  shares one branded flow.
- Replaced the hand-rolled `Field` component + inline `<textarea>` with the
  V2 `Input` / `Textarea` primitives (which carry label + hint + error +
  focus-visible wiring).
- Submit button → `<Button variant="brand" size="lg" className="w-full">`.
- Success state → `<EmptyState>` (keyhole motif) inside the same `AuthLayout`.
- Error banner → `bg-rose-50` + `border-rose-200` + `text-rose-700` instead of
  the legacy `bg-red-50`.
- Footer link → brand-orange `Sign in` link (matches Login's pattern).

## What was preserved
- All form state (`useState` shape), submit payload, `extractError` helper,
  and the `useEnquireMutation` wiring — pure UI port, no API surface change.
- Backend `/api/v1/enquire/` endpoint untouched.

## Continuous improvement
- The Enquire page no longer hand-rolls a form field or success card — both
  reuse system primitives. This is the second page (after Register) to
  successfully compose the `AuthLayout` shell, so the pattern is proven for
  any future external surface.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green
  (17 files / 89 tests).
- Grep `primary|indigo|blue-|gray-50|text-gray-` in the file → 0.

## Next
M5-02 per-surface responsive audit.
