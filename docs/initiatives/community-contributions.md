# Community Contributions — content, widgets, and the approval pipeline

> ## 🔒 Routine ownership
> This initiative is planned by the `openshiksha-plan` routine and built by
> `openshiksha-execute`. The AI-Native Interactive Learning initiative remains
> fenced to `openshiksha-ai-features` — reuse its guardrails (schema
> validation, sandbox, provenance) but never build inside its backlog.

**Status:** 🟢 Active (opened 2026-07-05, post-launch-video) · **Owner:** plan/execute routines

## North Star

Make OpenShiksha genuinely contributable: an outsider can (a) get productive in
minutes, (b) author **content packs** (questions/problem sets) and **widgets**
that are validated by construction, and (c) submit them through a pipeline
where the **maintainer approves in-app** — approved work lands in the question
bank with attribution; nothing external reaches students unreviewed.

Two tracks:

## Track A — Open-source friendliness (audit → fix)

Recurring audit against reality (not vibes): clone-to-running time, docs
truthfulness, contribution ergonomics. Known gaps from the OSS-readiness
initiative: issue/PR templates, architecture diagram, screenshots in README,
docs consolidation, good-first-issue seeding, widget SDK walkthrough.

| ID | Increment | Status |
|----|-----------|--------|
| OSS-1 | **Cold-clone audit**: follow README on a clean checkout (compose up, seed, run tests); fix every lie/missing step found; record time-to-running. | ✅ |
| OSS-2 | **Issue/PR templates + labels + first issues**. *(Grounded 2026-07-09: bug/feature/widget-proposal templates + PR-template-with-checklist already exist; real gaps below.)* (a) create the `widget-proposal` + `content-pack` labels the templates already reference (missing → GitHub drops them silently); (b) add a **content-pack proposal** issue form (propose/request content — submission stays the PR funnel); (c) seed `good first issue` on 5+ real, scoped issues. | ✅ |
| OSS-3 | **Widget SDK guide**: `docs/widgets.md` — `npm run widget:new` → schema → parity-guarded vendored copy → tests → registry PR, with one worked example. *(Shipped 2026-07-09 as `docs/widgets/README.md` — an index over the existing `build-your-first-widget`/`anatomy`/`review-bar` docs, since the SDK docs live in `docs/widgets/`, not a top-level `docs/widgets.md`.)* | ✅ |
| OSS-4 | **Architecture diagram + README screenshots** (from the demo stack; commit real PNGs, not promises). *(Verified 2026-07-09: already met — README carries a Mermaid diagram + ASCII fallback + tech table, and a Screenshots section backed by 3 real committed images under `docs/screenshots/`.)* | ✅ |
| OSS-5 | **Community docs**: CONTRIBUTING refresh pointing at both funnels (code/widgets vs content packs); link from README + landing page. | ⬜ |

> **Grounding (verified 2026-07-09 against `.github/`):** issue templates are
> legacy **markdown** (`bug_report.md`, `feature_request.md`,
> `widget_proposal.md`) with `blank_issues_enabled: false` + a security
> contact link; `pull_request_template.md` already carries the Type + How-tested
> + checklist (so OSS-2's "PR template with test checklist" is **already met**).
> Repo labels include `good first issue`, but **not** `widget-proposal` /
> `content-pack` — the widget template's `labels: widget-proposal` currently
> resolves to nothing (GitHub applies only labels that exist), so those issues
> land unlabeled. No open issue is tagged `good first issue` yet.
>
> **Content-pack issue form (decided 2026-07-09):** a `content-pack` issue form
> is a **proposal/coordination** surface (like `widget_proposal`), *not* a
> submission channel — packs are still authored as JSON and submitted via the
> `contrib/packs/` PR funnel (CP-5). The form asks: topic + grade band, rough
> question count, whether any widget *kind* is needed (link the widget funnel if
> a new kind is), a license/provenance heads-up, and "offering to author it?".
> This keeps one honest rule everywhere: **content is data via PR, code via
> review, issues are only for proposing.**

## Track B — Content pipeline: contribute → validate → approve → publish

The safety pattern mirrors DTB-1: **contributions are data, validated against
schemas, and never reach students without deterministic checks + human
approval.**

> **Grounding (verified 2026-07-06 against code):**
> - `validate_widget_config(kind, config)` lives at
>   `backend/openshiksha/apps/core/widgets.py:105` and raises a **DRF**
>   `serializers.ValidationError` (not a plain exception). CP-1's "pure"
>   validator must either wrap it into the pack's own error type or accept the
>   DRF coupling — decide in CP-1. Kind registry: `KNOWN_WIDGET_KINDS`; vendored
>   schemas at `apps/core/data/widget_schemas/*.schema.json` (6 kinds).
> - `Question` (`models.py:361`) has **no status field** — only `is_active`
>   (soft-delete) and `created_by` (audit); `school=null` = shared bank. So
>   pending content is a **separate `ContentSubmission` row**, not a flag on
>   Question.
> - Precedent to mirror: `TeacherWidgetVisibility.PENDING_REVIEW`
>   (`models.py:1133`) is already the repo's pending→review moderation state.

**CP-3 state machine (decided 2026-07-06):** a `ContentSubmission` row is one
imported pack in one of four states — `pending` (imported, awaiting review),
`approved` (questions materialized into the bank), `rejected` (archived with a
reviewer reason), `superseded` (a newer import of the same `pack_hash` replaced
it). Legal transitions: `pending→approved`, `pending→rejected`,
`pending→superseded`, `rejected→pending` (re-open). Approval and rejection are
**terminal for that row** (no approved→rejected un-publish; instead deactivate
the materialized questions via `is_active` and file a fresh submission).
Approval is idempotent — re-approving a materialized pack is a no-op keyed on
`pack_hash`. Reviewer + timestamp + note are recorded on every transition.

**Supersede is a review-time action, not import-computed (decided 2026-07-07):**
the CP-1 schema (`content_pack.schema.json`) carries **no stable pack identity** —
only the optional free-text `name` and `provenance.author`/`source`. A content
edit changes `pack_hash`, so import cannot reliably tell "a newer version of pack
X" from "a brand-new pack." Therefore `import_content_pack` (CP-2) **never
auto-transitions** an older row to `superseded`; it only ever creates a fresh
`pending` row or no-ops (see CP-2 idempotency below). `pending→superseded` is
triggered by the maintainer at review time (CP-3 API / CP-4 UI) when they
knowingly approve a replacement and want the stale pending row retired. (If a
stable `pack_id` is ever added to the schema, revisit auto-supersede — but that
is CP-1 v1.1 churn, out of scope here.)

| ID | Increment | Status |
|----|-----------|--------|
| CP-1 | **Content-pack schema** (the keystone): versioned JSON schema for a pack of questions/subparts (incl. `widget_kind`/`widget_config`, reusing the vendored widget schemas + `validate_widget_config`) + provenance block (author, source, license). Pure validator `backend/openshiksha/apps/core/content_packs.py` + schema `…/apps/core/data/content_pack.schema.json` + tests (valid/invalid per field class). No DB writes yet. | ✅ |
| CP-2 | **`manage.py import_content_pack <file> [--dry-run]`**: validates via CP-1 (`validate_content_pack`), stages the **whole pack as one `ContentSubmission`** row (state machine says *one row = one pack*, holding the full `payload`; the model already exists — T-3), `state=PENDING`, never touching the live bank. **Idempotency (decided 2026-07-07):** compute `content_pack_hash`; if a row with that `pack_hash` already exists in `PENDING` or `APPROVED`, no-op and report "already staged/approved"; otherwise create a `PENDING` row (so a previously `REJECTED`/`SUPERSEDED` pack can be re-staged). Never auto-supersedes (see the state-machine note). `--dry-run` validates + reports without writing. Tests: dry-run, import, re-import no-dupe, invalid rejected, re-import of rejected re-stages. | ✅ |
| CP-3 | **Submission review model + API**: `ContentSubmission` (pack metadata, state machine pending→approved/rejected, reviewer, notes) with admin-only endpoints; approving materializes the pack's questions into the bank (`school=null` shared bank, `created_by`=reviewer, attribution from the provenance block); rejecting archives with a reason. Mirror the existing `TeacherWidgetVisibility.PENDING_REVIEW` moderation precedent (`models.py:1133`). Tests incl. permission walls. | ✅ |
| CP-4 | **Review UI (admin)**: a "Submissions" queue page — pack summary, per-question preview (reusing the existing QuestionPreviewPanel/widget sandbox preview), Approve/Reject with note. The maintainer's one-click approval surface. | ✅ |
| CP-5 | **GitHub intake**: `contrib/packs/README.md` + example pack; CI job validating any `contrib/packs/*.json` on PRs (CP-1 validator) so external PRs self-check; on merge, maintainer runs/import lands them as pending (CP-2) for in-app approval (CP-4). | ✅ |
| CP-6 | **Widget proposal funnel**: issue form + `docs/widgets.md` section on the review bar (sandbox rules, schema, parity test, a11y); document that widget code ships only via normal code review (PRs), never via the content pipeline. | ✅ |

**Track B DoD:** an external contributor can PR a content pack; CI validates it
mechanically; after merge it imports as *pending*; the maintainer sees it in
the in-app queue, previews the actual rendered questions/widgets, clicks
Approve; the content appears in the question bank with attribution — and at no
point could unreviewed content reach a student. ✅ **Met (2026-07-07)** —
CP-1..6 shipped: schema+validator → CI-gated `contrib/packs/` intake →
`import_content_pack` staging → in-app review queue with real previews →
approve-materializes-with-attribution, plus the widget-code funnel fenced to
normal PR review throughout.

## Hard rules

- **Nothing external activates without human approval** (CP-3 state machine —
  the same "deterministic gate + honest provenance" philosophy as the AI work).
- Content is **data validated against schemas**; widget *code* goes through
  normal PR review only.
- Atomic PRs to `qa`; every increment ships with tests; reuse existing
  infra (widget schema validation, QuestionPreviewPanel, admin role walls).

## Task queue (plan appends · execute works top-down)

- [x] **T-1..T-5 (2026-07-05 → 07-07):** OSS-1 cold-clone audit + the whole
      Track-B build (CP-1 schema/validator, CP-3 model, CP-2 importer, CP-3 API +
      materialization). **All shipped — full detail in the Progress ledger.**
- [x] **T-6 (2026-07-09):** OSS-2 templates + labels. (a) Create two repo labels
      the existing templates already name so they stop resolving to nothing:
      `gh label create widget-proposal -c C5DEF5 -d "Proposal for a new widget kind"`
      and `gh label create content-pack -c 0E8A16 -d "Content-pack proposal / contribution"`
      (`widget_proposal.md` already carries `labels: widget-proposal`, so it will
      start applying once the label exists — verify). (b) Add
      `.github/ISSUE_TEMPLATE/content_pack.md` — a **proposal** form
      (`title: "[Content]: "`, `labels: content-pack`) per the decision above:
      topic + grade band, rough #questions, whether a new widget *kind* is needed
      (link `widget_proposal`), license/provenance heads-up, "offering to author?"
      checkbox — with a top comment that **submission is the `contrib/packs/` PR
      funnel, not this issue**. Verify: `gh label list` shows both; a test issue
      from each template lands with the right label. Docs/config only, no tests.
- [x] **T-7 (2026-07-09):** OSS-2 seed 5+ `good first issue`s. Source them from
      real, scoped, low-blast-radius gaps found while reading the tree (not
      invented) — e.g. a missing test, a small a11y label, a doc typo, a lint
      nit, a tiny copy fix. Each issue: clear title, a "why", the exact file(s),
      and acceptance criteria a newcomer can self-verify; apply `good first
      issue` (+ area label). File with `gh issue create`. Deliverable = the 5+
      issue URLs listed in the ledger. **Do not** file busywork or anything that
      needs deep context.

## Progress ledger

| Date | Increment | PR | Notes |
|------|-----------|----|----|
| 2026-07-05 | Initiative opened (post-launch-video pivot). Tracks A+B scoped; T-1/T-2 queued. | — | Launch video shipped 2026-07-05 (`launch-video-final3`, local-only asset); routines repurposed from the launch track to this initiative. |
| 2026-07-06 | Grounded CP-1/2/3 against code (real paths `backend/openshiksha/apps/core/…`; `validate_widget_config` raises DRF error; Question has no status field; `TeacherWidgetVisibility.PENDING_REVIEW` precedent). Decided CP-3 state machine (4 states). Queued T-3 (ContentSubmission model). | — | No external contributors waiting; execute has not yet started T-1/T-2. |
| 2026-07-06 | **CP-1 shipped** (T-2): `content_pack.schema.json` (v1.0, provenance required) + pure `content_packs.py` validator (structural + per-widget) + `content_pack_hash` + 24 tests. DRF `ValidationError` wrapped into pack-native `ContentPackError`. | [#514](https://github.com/openshiksha/openshiksha/pull/514) | No DB writes; unblocks CP-2. |
| 2026-07-06 | **CP-3 model shipped** (T-3): `ContentSubmission` + `ContentSubmissionState` + `transition_to()` state-machine guard (4 states, idempotent re-approval, reviewer/note/timestamp per transition); migration `0031`; 15 model tests. Model-only — API/materialization/UI still open under CP-3/CP-4. | [#515](https://github.com/openshiksha/openshiksha/pull/515) | One row = one pack (per decided state machine); flagged CP-2's "per question" wording as stale. |
| 2026-07-07 | Grounded CP-2 against the landed model + validator (`content_packs.py` exports `validate_content_pack`/`content_pack_hash`/`ContentPackError`; `ContentSubmission` holds whole-pack `payload`). Fixed CP-2's stale "per question" wording (now one PENDING row per pack). **Decided:** the schema has no stable pack id, so import **never auto-supersedes** — idempotency keys purely on `pack_hash`; `superseded` is a review-time transition only. Queued T-4 (CP-2 import command) + T-5 (CP-3 API + materialization). | — | Queue now T-1 (OSS-1), T-4 (CP-2), T-5 (CP-3 API) open. No external contributors waiting. |
| 2026-07-07 | **CP-2 shipped** (T-4): `import_content_pack <file> [--dry-run]` — validates via CP-1 and stages the whole pack as one `PENDING` `ContentSubmission`, never touching the live bank. Idempotency keyed on `pack_hash` (PENDING/APPROVED re-import is a no-op; REJECTED/SUPERSEDED can be re-staged); never auto-supersedes. 10 tests (accept/dry-run/idempotency/reject paths). | [#517](https://github.com/openshiksha/openshiksha/pull/517) | No new migration; `Question` untouched. Unblocks T-5 (CP-3 API + materialization). |
| 2026-07-07 | **CP-6 shipped** (user-directed session) — **Track B backlog complete, DoD met**. The widget-code funnel: `.github/ISSUE_TEMPLATE/widget_proposal.md` (labels `widget-proposal`; asks what-it-teaches, interaction sketch, answer-producing vs explanatory + gradeability of reported values, config fields, sandbox fit, a11y plan, build-offer) + `docs/widgets/review-bar.md` — the reviewer's checklist grounded in the real rules: sandbox constraints (no network/imports/closures/eval, deterministic, AI never in-sandbox), both schema copies + the `TestWidgetSchemaParity` guard + `KNOWN_WIDGET_KINDS`, answer-reporting rules (no report at mount, grader-markable precision — the ¾ bug class, widget reports / grader decides), keyboard + ARIA a11y, Vitest/pytest expectations incl. the anti-drift pattern for inlined engines. CONTRIBUTING gains a "Ways to contribute content & widgets" section routing **data → content packs, code → PR review** (the CP-6 fence, now stated everywhere a contributor lands: CONTRIBUTING, the pack README, the review bar, the issue form itself). Docs-only — no code paths changed. | (this session) | The doc-scoped `docs/widgets.md` in the backlog didn't exist — the SDK docs live in `docs/widgets/` (anatomy + build-your-first-widget), so the review bar landed beside them as `review-bar.md` rather than inventing a new top-level file. Note the initiative's remaining open work is now **Track A only** (OSS-1..5). |
| 2026-07-07 | **CP-5 shipped** (user-directed session): the GitHub intake funnel. New DB-free `manage.py validate_content_pack <files…>` (per-file ✓/✗ with the CP-1 validator's location-scoped errors verbatim, echoes question count + `pack_hash` prefix so a merged PR is traceable to its later submission row, non-zero exit on any failure) — the seam CP-1's docstring reserved for CI. `contrib/packs/README.md` (author → PR → CI self-check → merge → `import_content_pack` → in-app approval, format essentials, local-validation one-liner, data-not-code ground rules) + `contrib/packs/example-fractions-pack.json` (MCQ + number-line widget subpart). New `content-packs.yaml` workflow validates `contrib/packs/*.json` on PRs touching packs/schema/validator. 9 backend tests, incl. a guard that **every shipped `contrib/packs/*.json` must validate** so the documented example can never rot. | (this session) | Validation stays read-only by design: merging a pack PR still publishes nothing — CP-2 staging + CP-4 approval remain the human gates, so CI green ≠ content live. Splitting a DB-free `validate_content_pack` command out of `import_content_pack --dry-run` (which queries `ContentSubmission` for idempotency) keeps the CI job migration-free. |
| 2026-07-07 | **CP-4 shipped** (user-directed session, not a routine run): admin "Content Submissions" page at `/admin/submissions` (`SubmissionsPage` + `useContentSubmissions` hooks, ADMIN-walled route, linked from AdminDashboard). Queue filtered by state (pending default); detail shows the provenance block (author/license/source — what approval publishes with), per-question preview via a pure `packQuestionToPreview` mapper into the **existing `QuestionPreviewPanel`** (zero parallel preview code; defaults mirror the importer's mcq/difficulty-2), and widget-bearing subparts render in the **real `InteractiveWidget` sandbox**. Approve/Reject with note (reject blocks locally without one; the backend requires it too), Reopen for rejected; all legality stays server-side — a 409 from `transition_to()` is surfaced verbatim. 24 new frontend tests (hooks: URL shapes/pagination-unwrap/enabled-gate/409; page: filter default+switch, provenance+preview+sandbox render, approve/reject/reopen flows, note-required, 409 surfaced, approved read-only; mapper: mapping + importer defaults). | (this session) | The preview trusts the payload with no client-side re-validation — CP-1 validated it at import, mirroring how DTB-3 trusted DTB-1/2's contract. Widget preview reuses the same sandboxed `InteractiveWidget` students see, so a reviewer approves exactly what will render. |
| 2026-07-09 | **OSS-1 shipped** (T-1): cold-clone audit. Fixed a hard `docker compose up` crash on fresh clones — the `frontend` service required the gitignored `frontend_modern/.env` (Quickstart never created it); marked that env_file `required: false` (the `environment:` block already supplies the needed VITE_* vars), verified `docker compose config` now passes cold. README Quickstart corrected: compose runs the **full stack incl. frontend at :5173** (was falsely "Backend + Postgres + Redis + Celery" with a colliding separate `npm run dev`); host `npm run dev` demoted to an optional faster-HMR path. `backend/.env.example` gained a commented, blank AI block so the "AI key optional" note stops pointing at a missing field. Docs/config only — no code paths, no tests. | [#523](https://github.com/openshiksha/openshiksha/pull/523) | Track A now OSS-2..5 open. Time-to-running was audited statically (no full image build in the scheduled run); the fix removes the only `up`-time blocker so the path is followable end-to-end. |
| 2026-07-07 | **CP-3 shipped** (T-5): admin-only `ContentSubmissionViewSet` (list/detail + approve/reject/reopen driving `transition_to`) + `content_submissions.py` `materialize_submission()` — approve creates shared-bank `Question` rows (`school=None`, `created_by`=reviewer), idempotent on `pack_hash` via a `content-pack:<hash>` marker tag. Illegal transitions → 409; reject requires a note. 13 API tests (permission walls + materialize + idempotent re-approve). Stacked on #517. | [#518](https://github.com/openshiksha/openshiksha/pull/518) | **Discrepancy:** `Question` has no attribution column → attribution carried by `created_by` + the marker tag → `ContentSubmission.provenance`; first-class attribution field deferred to a future migration. CP-4 (review UI) is the next Track-B step. |
| 2026-07-09 | **OSS-3 + OSS-4 shipped.** OSS-3: added [`docs/widgets/README.md`](../widgets/README.md) — a single SDK-guide entry point tying together the proposal issue → `build-your-first-widget` (the `widget:new` → schema → backend-mirror → verify walkthrough) → `anatomy` (the `defineWidget`/sandbox reference) → `review-bar` (the bar), with the honest **data-via-pack / code-via-PR** fence at the top and a table of the 7 real widget kinds (types verified against each `index.ts`'s `answerProducing`). Fixed a stale lie in `anatomy.md` ("the two widgets shipping on `modernization` today" — `modernization` is deleted, there are now 7 kinds on `qa`). Linked both funnels from the README Documentation index. OSS-4: verified already-met — README's Mermaid diagram + ASCII fallback + tech table and the 3 committed `docs/screenshots/*` images (real JPEG/PNG, git-tracked, 1000×1925 / 2560×1253 / 1425×1146) satisfy it; no code change needed. Both → ✅. | [#530](https://github.com/openshiksha/openshiksha/pull/530) | Realised OSS-3 as a folder index rather than a new top-level `docs/widgets.md`, matching where the SDK docs already live (same call as CP-6's `review-bar.md`). Only **OSS-5** (community-docs discoverability) remains before Track A — and the whole initiative — closes. |
| 2026-07-09 | **OSS-2 shipped** (T-6 + T-7). T-6: created the two repo labels the templates already named (`widget-proposal` #C5DEF5, `content-pack` #0E8A16) so the widget template's `labels:` line now resolves; added `.github/ISSUE_TEMPLATE/content_pack.md` — a **proposal/coordination** form (`title: "[Content]: "`, `labels: content-pack`) with a top comment stating submission is the `contrib/packs/` PR funnel, not the issue (topic+grade band, rough size, new-widget-kind gate linking the widget funnel, license/provenance, "offering to author?"). T-7: seeded **5** real, scoped `good first issue`s sourced from the tree — 4 missing-test gaps on untested `shared/ui` primitives ([#524](https://github.com/openshiksha/openshiksha/issues/524) Button, [#525](https://github.com/openshiksha/openshiksha/issues/525) Badge, [#526](https://github.com/openshiksha/openshiksha/issues/526) Card, [#527](https://github.com/openshiksha/openshiksha/issues/527) Skeleton) + 1 real a11y bug ([#528](https://github.com/openshiksha/openshiksha/issues/528) `Logo` full-variant announces "OpenShiksha" twice: img `alt` + wordmark). Each carries a why, exact file(s), and self-verifiable acceptance criteria. OSS-2 → ✅. | [#529](https://github.com/openshiksha/openshiksha/pull/529) | Labels/issues created directly via `gh` (not in-repo). No doc-typo issue filed — grepped docs for common misspellings and found none (won't invent busywork). Track A now OSS-3..5 open (widget SDK guide, arch diagram + screenshots, CONTRIBUTING refresh). |
| 2026-07-09 | **Track B complete → Track A engaged.** Grounded OSS-2 against `.github/`: bug/feature/widget-proposal templates + the PR-template-with-checklist already exist (that OSS-2 clause is **met**); real gaps are the missing `widget-proposal`/`content-pack` labels (the widget template names one that doesn't exist, so it applies nothing) and zero seeded `good first issue`s. **Decided** the `content-pack` issue form is a *proposal* surface, not a submission channel (submission stays the `contrib/packs/` PR funnel). Marked OSS-2 🔶; collapsed the T-1..T-5 done-detail into the ledger; queued **T-6** (labels + content-pack proposal template) and **T-7** (seed 5+ good-first-issues). | — | No external contributors waiting (2 open issues, both maintainer enhancements). Queue: T-6, T-7 open. |
