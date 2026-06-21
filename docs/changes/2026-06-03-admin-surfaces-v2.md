# 2026-06-03 — Admin Dashboard + Classroom manage migrated to V2

## Summary
Migrated `AdminDashboard.tsx`, `ClassroomManagePage.tsx`, and
`EnrollStudentsModal.tsx` to V2 "Chalk & Unlock". Stat tiles now use the
`<Stat>` primitive, the modal uses `.os-card` chrome, and form fields use
`ui/Input`/`Select`.

## Classification
Improve — reskin only. Hooks, role guards, mutations unchanged.

## What changed
- Summary tiles → `<Stat>` (font-display value, ink-400 label).
- Forms wrapped in `<Card>`; subject-room mini-form on warm `bg-paper`.
- Indigo/red/gray classes → brand/rose/ink tokens.
- Buttons → `<Button variant="brand"|"ghost">`.
- Empty states → `<EmptyState>` keyhole motif.
- ClassroomRow gets keyboard activation (Enter/Space) + focus-visible ring + warm hover.
- Modal: black/40 → ink-900/40 backdrop; close-icon uses ink-* hovers.
- EnrollStudentsModal preserved every query hook used by tests
  (search placeholder, "Enroll"/"Remove" button names, label structure containing
  student names) — test file unchanged, 84/84 still green.

## Tests
- type-check / lint / build / vitest 84/84 — green.

## Verify
`admin_demo` / `demo1234` → /admin, open a classroom, click "Manage students".

## Next
PRs 4–5 will migrate Proficiency cluster and Assignment/SRS surfaces.
