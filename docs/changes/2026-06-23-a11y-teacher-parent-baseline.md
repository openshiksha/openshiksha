# 2026-06-23 — A11Y-9: authenticated axe harness for teacher + parent surfaces (baseline)

## Summary
Opens **Accessibility Batch 3** (teacher / parent surfaces) by extending the
authenticated per-route axe harness — built for the student core loop in A11Y-6 —
to the **teacher and parent** roles. Adds the teacher dashboard, question bank, AI
grading queue, and parent dashboard to the route table in **reporting-mode**. This
PR establishes the violation inventory a follow-up remediates and gates.

## Classification
**New** — test-harness infra + role fixtures. No app/source changes.

## What changed
- `frontend_modern/e2e/support/auth.ts`:
  - Generalized the single-role harness into a role-parametrized one. Added
    `TEACHER_USER`, `PARENT_USER`, and a `CHILD_USER` the parent surfaces resolve
    via `/users/me/children/`.
  - `routeHandler` → `makeRouteHandler(user)` (a closure): only the identity reads
    (`/users/me/`, `/users/me/children/`) vary by role; the list reads are
    role-agnostic (the backend scopes by JWT, which we stub).
  - Exposes `setupStudentAuth` / `setupTeacherAuth` / `setupParentAuth` and an
    `AUTH_SETUP` role→helper map for the parameterized spec.
- `frontend_modern/e2e/a11y.spec.ts`:
  - `auth?: boolean` → `auth?: 'student' | 'teacher' | 'parent'`; existing student
    routes updated to `auth: 'student'`.
  - Added four reporting-mode routes: `/teacher`, `/teacher/questions`,
    `/teacher/grading`, `/parent`.

## Baseline inventory (this PR's output)
`npx playwright test a11y` → **15 passed**. New routes:
- `/teacher`, `/teacher/questions`, `/teacher/grading` — **structurally clean**,
  `blocking: []`. Only `color-contrast` in the non-gating `incomplete` bucket.
- `/parent` — **one blocking `color-contrast`**: the "View insights" link renders
  `text-brand-700` (`#C05300`) on `bg-brand-50` (`#FFF8F1`) → 4.45 : 1, a hair
  under AA's 4.5 : 1. A11Y-4 verified `brand-700` against pure white (≥ 4.5 : 1)
  but not against the warm `brand-50` tint. This is the single finding the next
  remediation PR fixes before `/parent` can be gated.

## Tests
- `npx playwright test a11y` — 15 passed (reporting mode). `npx tsc --noEmit` +
  `eslint e2e/ --max-warnings 0` clean.

## Migration notes
None. Test-only.

## Next steps
- **A11Y-10** — remediate the `/parent` `brand-700`-on-`brand-50` contrast finding.
- **A11Y-11** — flip the now-clean teacher (+ remediated parent) routes to
  `gate: true` + Batch 3 close-out.
