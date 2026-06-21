# 2026-06-20 — A11Y-6: Authenticated axe harness + student core-loop baseline

## Summary
Extends the per-route axe audit behind a stubbed student session so the
authenticated **student core loop** (dashboard, assignment detail, proficiency,
SRS drill) is measured for the first time. Reporting-mode — this PR establishes
the violation inventory that A11Y-7 remediates and A11Y-8 gates.

## Classification
**New** — net-new test harness infra. No app/source changes.

## What changed
- `e2e/support/auth.ts` (new): `setupStudentAuth(page)` seeds the JWT keys the
  app reads (`access_token` / `refresh_token`) via `addInitScript`, then
  `page.route('**/api/v1/**', …)` fulfils every core-loop read with tiny static
  fixtures (current user, streak, assignment list + detail with subparts, a
  non-submitted submission, proficiency, an SRS drill). Object endpoints that
  mean "nothing yet" (`/ai/practice-plans/today/`, `/push/vapid-public-key/`)
  return 404 so their hooks map to null/disabled; all other unmatched reads
  return an empty paginated page. The CI `frontend-e2e` job runs `vite preview`
  with **no backend**, so this stubs the session rather than logging in.
- `e2e/a11y.spec.ts`: added an optional `auth?: boolean` to the route table and
  four student routes (`/student`, `/student/assignments/1`,
  `/student/proficiency`, `/student/srs-drill/1`) in **reporting-mode**
  (`gate: false`). When `auth`, the test applies `setupStudentAuth` before
  `page.goto`.

## Baseline inventory (this PR's output)
All four student routes come back **structurally clean** — no label, landmark,
or heading violations. The only blocking finding is `color-contrast` (4 nodes),
and two of the four are already resolved by **A11Y-4** (`.btn-brand` and small
`text-brand-700` text). The remaining two are the `StreakBadge` secondary
labels rendered in shared chrome (`opacity-70` / `opacity-60` amber spans,
2.9–3.6 : 1) — **A11Y-7's** target.

## Legacy reference
None — net-new.

## Tests / how to verify
- `npm run type-check` + `npm run lint` — green.
- `npx playwright test a11y` — all routes pass (7 public + 4 student) in
  reporting mode; the student inventory lands in `axe-report/student-*.json`.

## Next steps
- A11Y-7: remediate the `StreakBadge` contrast finding.
- A11Y-8: once A11Y-4 + A11Y-7 are merged and the student routes compute clean,
  flip them to `gate: true`. (Gating before then would red-wall CI on the
  pre-existing brand/streak contrast.)
