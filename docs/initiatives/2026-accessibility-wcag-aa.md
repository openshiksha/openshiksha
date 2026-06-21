# Accessibility — WCAG 2.1 AA

> **Status:** Active (promoted 2026-06-19) · **Owner routine:** `openshiksha-execute`
> · **Tracking board:** [STATUS.md](STATUS.md) · **Batch 1 plan:**
> [2026-06-19-plan.md](../daily-plans/2026-06-19-plan.md)

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
4. *(future batch)* **Student core-loop surfaces** (assignment detail, dashboard,
   SRS drill, proficiency) remediated + gated.
5. *(future)* **Keyboard-only walkthrough + screen-reader spot-check** (NVDA /
   VoiceOver) sign-off.
6. *(future)* **Teacher / parent surfaces** remediated + gated; consider an axe CI
   job that scans authenticated routes against the Docker stack.

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
| A11Y-5 (this batch) | Gate clean public routes + close-out | New + Docs | Recorded axe `incomplete`; gated `/login`, `/register`, `/register/school`, `/register/open`, `/enquire` (`gate: true`); `/` + `/design` stay reporting-mode; change doc + manual checklist. |
