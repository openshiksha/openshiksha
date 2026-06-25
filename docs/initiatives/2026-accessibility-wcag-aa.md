# Accessibility — WCAG 2.1 AA

> **Status:** ✅ **Closed (2026-06-25)** — all six DoD items met. Item 5's
> keyboard sign-off is automated + gated; its human NVDA/VoiceOver listen-through
> is **formally waived by the project owner** (no screen-reader tester available),
> with the automatable slice standing in (see DoD item 5). Promoted 2026-06-19 ·
> **Owner routine:** `openshiksha-execute` · **Tracking board:** [STATUS.md](STATUS.md)
> · **Batch 1 plan:** [2026-06-19-plan.md](../daily-plans/2026-06-19-plan.md)

## North Star

Every **public** and **student-core** surface passes axe-core WCAG 2.1 AA with
**zero serious/critical violations, enforced in CI**, and keyboard-only and
screen-reader users can complete the core journeys (sign in, register, browse,
practice, submit). Accessibility is a **measured, regression-gated contract** —
not an aspiration.

## Why now

OpenShiksha serves K-12 students, teachers, and parents across a huge ability and
device range in India: low-vision users, keyboard-only users, screen-reader users,
and budget Android browsers. Accessibility here is not polish — it is **access**.

The V2 design system already commits to "Accessible by default"
([`2026-design-system-v2.md`](2026-design-system-v2.md) principle #7); this
initiative turns that claim into something **measured and enforced**.

The runway already exists — we are **activating** it, not inventing it:

- devDeps `@axe-core/playwright` + `axe-core` are already present.
- `e2e/a11y.spec.ts` already runs axe — but only on `/design`, in **reporting
  mode** (`FAIL_ON_BLOCKING = false`).
- CI's `frontend-e2e` job already runs `npm run test:e2e` and uploads the axe
  report as an artifact; `deploy` gates on `frontend-e2e`.
- **M6-01 (#202)** shipped a *focused* baseline (skip link + `#main-content`
  landmark in `AppShell`, dialog semantics on the QuestionBank side-sheet, image
  alt parity) and **explicitly deferred** the full audit "for a dedicated a11y
  initiative." **This is that initiative.**

## What exists / what to preserve

- The M6-01 foundation: skip link, `#main-content` landmark, dialog pattern.
- The V2 token system (warm paper / `ink-*`, `brand-600`) and the LA i18n
  registry (en/hi/mr) — new labels localize through it for free.
- The existing Playwright `frontend-e2e` CI job + axe artifact upload.

There is nothing to *port*: legacy Django 1.11 templates had no a11y story at all
(no ARIA, no contrast discipline, no automated checking). This is **net-new
platform capability**.

## Definition of Done (phased)

1. **Per-route axe baseline measured** across the public surfaces (reporting mode).
   *(A11Y-1)*
2. **Static `eslint-plugin-jsx-a11y` lint gate** catches a11y regressions at lint
   time, CI-enforced at `--max-warnings 0`. *(A11Y-2)*
3. **Public surfaces remediated** to zero serious/critical blocking violations and
   **gated** (`gate: true`) so the gain can't regress. *(A11Y-3, A11Y-4, A11Y-5)*
4. **Student core-loop surfaces** (assignment detail, dashboard, SRS drill,
   proficiency) remediated + gated. ✅ *(Batch 2 — A11Y-6/7/8, 2026-06-20..23)*
5. **Keyboard-only walkthrough + screen-reader spot-check** sign-off. ✅
   *(Batch 4 — A11Y-17 + A11Y-16/18, 2026-06-24..25.)* The **keyboard** half is
   automated and gated: `e2e/keyboard.spec.ts` drives the skip-link bypass
   (2.4.1), focus order (2.4.3), and focus-visible (2.4.7) with real Tab/Enter —
   the operability axe cannot test. The **screen-reader** half: the manual NVDA /
   VoiceOver listen-through (`a11y/screen-reader-signoff.md`) is **formally
   waived** by the project owner — no screen-reader tester is available — and the
   automatable slice stands in: axe's name/role/label rules gate every surface,
   and the sign-off doc's announce-region inventory verifies `role=status` /
   `aria-live` semantics on each live region. The live human pass is the one
   un-exercised check and is recorded as such (the journey tables are left
   unticked, **not** claimed as passed).
6. **Teacher / parent surfaces** remediated + gated. ✅ *(Batch 3 — A11Y-9/11/12
   + A11Y-13/15, 2026-06-23..24: the teacher dashboard/question-bank/grading +
   parent dashboard, **plus** the dense authoring forms — `CreateQuestionPage`,
   `CreateAssignmentPage`, `CreateProblemSetPage` — and the parent insights pages
   are all gated (`blocking === []`). The authoring-form baseline came back clean:
   the forms compose from the shared labelled `Input`/`Select`/`Textarea`
   primitives, so the anticipated labelling/heading remediation surface was empty.)*
   Consider an axe CI job over authenticated routes against the Docker stack.

## Phase / batch plan

- **Batch 1 (A11Y-1..5)** — *this batch, 2026-06-19*: per-route axe baseline →
  static jsx-a11y gate → structural (label/landmark/heading) + colour-contrast
  remediation on the public surfaces → **gate the clean routes**. Establishes the
  measured, CI-enforced AA contract. (DoD items 1–3.)
- **Batch 2** — student core-loop surfaces: remediate + gate. (DoD item 4.)
- **Batch 3** — teacher / parent surfaces: remediate + gate. (DoD item 6.)
- **Batch 4** — keyboard-only + screen-reader sign-off. (DoD item 5.)

## Per-route axe harness contract

`e2e/a11y.spec.ts` iterates a route table. Each entry:

```ts
{ name: 'login', path: '/login', gate: false }
```

For each route the spec navigates, waits for `networkidle` + `document.fonts.ready`
+ a visible `h1`, runs `AxeBuilder().withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa'])`,
and writes `axe-report/<name>.json` (summary + full violations). When `gate: true`
the spec **asserts zero serious/critical violations** for that route, turning the
`frontend-e2e` CI job into a regression gate. When `gate: false` it only records
(reporting mode). Adding a new surface to the audit = one row in the table; locking
it in = flip that row's `gate` once it's clean.

## Ledger

| PR | Increment | Class | Summary |
|---|---|---|---|
| [#389](https://github.com/openshiksha/openshiksha/pull/389) | A11Y-1 — initiative doc + per-route axe baseline | New | This doc + parameterized `e2e/a11y.spec.ts` emitting per-route `axe-report/<route>.json` (reporting mode). |
| [#390](https://github.com/openshiksha/openshiksha/pull/390) | A11Y-2 — `eslint-plugin-jsx-a11y` static gate | New | `flatConfigs.recommended` wired into flat ESLint config; npm `overrides` for the stale eslint peer; 11 hits fixed; `--max-warnings 0` green. |
| — | A11Y-3 — form-label / landmark / heading fixes | — | **No remediation needed.** Baseline found the public/auth surfaces structurally clean (0 label/landmark/heading violations). Only `/design`'s widget-iframe range inputs lack labels (known-noise). |
| — | A11Y-4 — colour-contrast remediation | **Deferred** | One systemic finding: `.btn-brand` (white on `#FF6F00`, ≈ 2.8 : 1) fails AA enabled. Needs a **brand-shade design decision** before the mechanical fix — see [change doc](../changes/2026-06-19-a11y-batch1.md). |
| [#391](https://github.com/openshiksha/openshiksha/pull/391) | A11Y-5 — gate clean public routes + Batch 1 close-out | New + Docs | Recorded axe `incomplete`; gated `/login`, `/register`, `/register/school`, `/register/open`, `/enquire` (`gate: true`); `/` + `/design` stayed reporting-mode; change doc + manual checklist. |
| [#417](https://github.com/openshiksha/openshiksha/pull/417) | A11Y-4 — brand-shade decision + contrast token sweep (resolves the deferred row above) | Improve | Retuned `brand-700 → #C05300` (≥ 4.5 : 1 white); `.btn-brand` + small brand-text repainted; contrast rules documented; `/` (home) flipped to `gate: true`. |
| [#418](https://github.com/openshiksha/openshiksha/pull/418) | A11Y-FV — keyboard focus-visible indicator pass | Improve | Shared `:focus-visible` outline/ring token across the interactive primitives + bottom-tab/drawer/skip-link chrome (WCAG 2.4.7). |
| [#419](https://github.com/openshiksha/openshiksha/pull/419) | A11Y-6 — authenticated axe harness + student core-loop baseline | New | `e2e/support/auth.ts` (stubbed student JWT + `page.route` core-loop fixtures) + four `auth: true` student routes added to the table (reporting-mode). Baseline came back structurally clean. |
| [#420](https://github.com/openshiksha/openshiksha/pull/420) | A11Y-7 — student core-loop contrast remediation | Improve | Removed `opacity-70`/`opacity-60` from `StreakBadge` secondary labels (the one blocking finding the A11Y-6 inventory surfaced); hierarchy now carried by weight, contrast clears AA. |
| [#441](https://github.com/openshiksha/openshiksha/pull/441) | A11Y-8 — gate the student core-loop routes + Batch 2 close-out | New + Docs | Flipped `/student`, `/student/assignments/:id`, `/student/proficiency`, `/student/srs-drill/:entryId` to `gate: true` (all `blocking === []`); change doc + student-loop manual checklist; **DoD item 4 done**. |
| [#442](https://github.com/openshiksha/openshiksha/pull/442) | A11Y-9 — authenticated axe harness for teacher + parent surfaces (Batch 3 baseline) | New | Role-parametrized the harness (`TEACHER_USER`/`PARENT_USER`/`CHILD_USER` + `makeRouteHandler`); added `/teacher`, `/teacher/questions`, `/teacher/grading`, `/parent` (reporting). Teacher surfaces clean; `/parent` flagged one contrast node. |
| [#450](https://github.com/openshiksha/openshiksha/pull/450) | A11Y-11 — brand-text-on-tint contrast remediation | Improve | Small `brand-700` text on the `brand-50` tint is 4.45 : 1 (under AA); moved the `/parent` "View insights" link + the `AssignmentList` brand badge to `brand-800`; documented the rule. `/parent` → `blocking: []`. |
| [#451](https://github.com/openshiksha/openshiksha/pull/451) | A11Y-12 — gate the teacher + parent routes + Batch 3 close-out | New + Docs | Flipped `/teacher`, `/teacher/questions`, `/teacher/grading`, `/parent` to `gate: true` (all `blocking === []`); change doc + teacher/parent manual checklist; **DoD item 6 (partial) — teacher/parent core surfaces gated**. |
| A11Y-13/15 (this batch) | Baseline + gate the authoring forms + parent insights + ClassroomCodeWidget crash fix | New + Improve + Docs | Added `/teacher/questions/new`, `/teacher/assignments/new`, `/teacher/problem-sets/new`, `/parent/insights`, `/parent/insights/:childId` to the harness; baseline came back `blocking === []` (forms use the shared labelled primitives), so the planned A11Y-14 remediation was a no-op and the rows gate directly. Also stubbed the bare-array `/users/me/classroom-code/` read so the dashboard's `ClassroomCodeWidget` renders (a previously-uncovered crash under the catch-all). **DoD item 6 fully met.** |
| [#455](https://github.com/openshiksha/openshiksha/pull/455) | A11Y-17 — keyboard gate spec + screen-reader sign-off scaffold | New + Docs | `e2e/keyboard.spec.ts` (skip-link bypass, focus order, focus-visible); `a11y/screen-reader-signoff.md` manual script + announce-region inventory; post-submit score announced via `role=status` on `AssignmentDetailPage` (asserted in its offline test). |
| A11Y-16 (this batch) | Repair the mis-baselined Batch-3 rows | Fix | A11Y-13/15 gated `/teacher/questions/new` + `/parent/insights` but neither was actually clean: `CreateQuestionPage` renders **raw `<select>`** (not the shared `Select`), so the route carried 4 `select-name` criticals + 1 `brand-700`-on-tint contrast node; and the single-child insights landing redirected to the child detail, tripping the deep-link URL guard. Fixed with aria-labels on the raw selects + `brand-700 → brand-800` (the A11Y-11 rule), and audited the landing with two children (`parentMultiChild`). All 23 a11y/keyboard/deep-link e2e green. |
| A11Y-18 (this batch) | Batch 4 close-out — close the initiative | Docs | Flipped initiative **Status → Closed**; DoD item 5 marked met (keyboard automated + gated; the human screen-reader listen-through **waived** by the project owner, automatable coverage standing in); recorded the waiver in the sign-off doc + a change doc. |
