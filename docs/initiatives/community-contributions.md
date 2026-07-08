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
| OSS-1 | **Cold-clone audit**: follow README on a clean checkout (compose up, seed, run tests); fix every lie/missing step found; record time-to-running. | ⬜ |
| OSS-2 | **Issue/PR templates + labels**: bug/feature/widget-proposal/content-pack issue forms; PR template with test checklist; seed `good first issue` labels on 5+ real, scoped issues. | ⬜ |
| OSS-3 | **Widget SDK guide**: `docs/widgets.md` — `npm run widget:new` → schema → parity-guarded vendored copy → tests → registry PR, with one worked example. | ⬜ |
| OSS-4 | **Architecture diagram + README screenshots** (from the demo stack; commit real PNGs, not promises). | ⬜ |
| OSS-5 | **Community docs**: CONTRIBUTING refresh pointing at both funnels (code/widgets vs content packs); link from README + landing page. | ⬜ |

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
| CP-5 | **GitHub intake**: `contrib/packs/README.md` + example pack; CI job validating any `contrib/packs/*.json` on PRs (CP-1 validator) so external PRs self-check; on merge, maintainer runs/import lands them as pending (CP-2) for in-app approval (CP-4). | ⬜ |
| CP-6 | **Widget proposal funnel**: issue form + `docs/widgets.md` section on the review bar (sandbox rules, schema, parity test, a11y); document that widget code ships only via normal code review (PRs), never via the content pipeline. | ⬜ |

**Track B DoD:** an external contributor can PR a content pack; CI validates it
mechanically; after merge it imports as *pending*; the maintainer sees it in
the in-app queue, previews the actual rendered questions/widgets, clicks
Approve; the content appears in the question bank with attribution — and at no
point could unreviewed content reach a student.

## Hard rules

- **Nothing external activates without human approval** (CP-3 state machine —
  the same "deterministic gate + honest provenance" philosophy as the AI work).
- Content is **data validated against schemas**; widget *code* goes through
  normal PR review only.
- Atomic PRs to `qa`; every increment ships with tests; reuse existing
  infra (widget schema validation, QuestionPreviewPanel, admin role walls).

## Task queue (plan appends · execute works top-down)

- [ ] **T-1 (2026-07-05):** OSS-1 cold-clone audit — follow README verbatim on a
      fresh clone; log every failure/missing step; fix the README (+ compose
      docs) in one PR; record time-to-running in the PR description.
- [x] **T-2 (2026-07-05):** CP-1 content-pack schema + pure validator + tests
      (`backend/openshiksha/apps/core/content_packs.py`,
      `backend/openshiksha/apps/core/data/content_pack.schema.json`). Reuse
      `validate_widget_config` (widgets.py:105) for widget-bearing subparts —
      note it raises DRF `ValidationError`; decide whether to wrap. No DB writes.
- [x] **T-3 (2026-07-06):** CP-3 `ContentSubmission` model only (no API/UI yet) —
      fields per the state machine above (`pack_hash`, `provenance` JSON,
      `state`, `reviewer` FK, `note`, timestamps); migration + model tests for
      the legal/illegal transitions. Mirror `TeacherWidgetVisibility` for the
      state `TextChoices`. Cheap, low-risk table that unblocks CP-2/CP-4.
      **Done.** Added `ContentSubmissionState` TextChoices + `ContentSubmission`
      model with a `transition_to()` guard enforcing the four-state machine
      (pending→approved/rejected/superseded, rejected→pending reopen; approved &
      superseded terminal), idempotent same-state re-approval, and
      reviewer/note/`reviewed_at` recorded per transition. Migration
      `0031_contentsubmission`; 15 model tests.
- [x] **T-4 (2026-07-07):** CP-2 `manage.py import_content_pack <file>
      [--dry-run]` — the first writer into `ContentSubmission`. Validate with
      `validate_content_pack` (raise/report `ContentPackError` cleanly); stage the
      **whole pack as one PENDING row** (`name`, `pack_hash=content_pack_hash(pack)`,
      `provenance`, `payload`); idempotency keyed on `pack_hash` (skip if a
      PENDING/APPROVED row exists, else create). Never touches Question. Command
      at `backend/openshiksha/apps/core/management/commands/import_content_pack.py`;
      tests in the core test suite (dry-run, import, re-import no-dupe, invalid
      rejected, rejected-re-stages). No new migration.
- [x] **T-5 (2026-07-07):** CP-3-proper — admin-only DRF endpoints over
      `ContentSubmission` (list/detail + approve/reject/reopen actions calling
      `transition_to()` with the acting admin as `reviewer`) **plus**
      materialization on approve: create shared-bank `Question` rows
      (`school=null`, `created_by`=reviewer, attribution from `provenance`) from
      `payload`, idempotent on re-approve (keyed on `pack_hash`). Reuse the
      existing admin role wall (`UserRole.ADMIN`); mirror the
      `TeacherWidgetVisibility.PENDING_REVIEW` moderation precedent. Tests incl.
      permission walls + "approved content is now in the bank / re-approve is a
      no-op." **Depends on T-4** landing first.
      **Done.** `ContentSubmissionViewSet` (admin wall = `IsSchoolAdmin`) with
      list/detail + `approve`/`reject`/`reopen` actions; `content_submissions.py`
      `materialize_submission()` creates shared-bank questions and is idempotent
      via a `content-pack:<pack_hash[:16]>` marker `QuestionTag`. Illegal
      transitions → 409; reject requires a note. 13 API tests.
      **Discrepancy noted:** `Question` has **no attribution column**, so
      "attribution from provenance" is carried by (a) `created_by`=reviewer and
      (b) the marker tag linking each question back to the `ContentSubmission`
      row, which permanently retains the full `provenance` block. A first-class
      attribution field on `Question` is a deliberate future migration (would
      also let CP-4 surface author/license inline) — out of scope for T-5.

## Progress ledger

| Date | Increment | PR | Notes |
|------|-----------|----|----|
| 2026-07-05 | Initiative opened (post-launch-video pivot). Tracks A+B scoped; T-1/T-2 queued. | — | Launch video shipped 2026-07-05 (`launch-video-final3`, local-only asset); routines repurposed from the launch track to this initiative. |
| 2026-07-06 | Grounded CP-1/2/3 against code (real paths `backend/openshiksha/apps/core/…`; `validate_widget_config` raises DRF error; Question has no status field; `TeacherWidgetVisibility.PENDING_REVIEW` precedent). Decided CP-3 state machine (4 states). Queued T-3 (ContentSubmission model). | — | No external contributors waiting; execute has not yet started T-1/T-2. |
| 2026-07-06 | **CP-1 shipped** (T-2): `content_pack.schema.json` (v1.0, provenance required) + pure `content_packs.py` validator (structural + per-widget) + `content_pack_hash` + 24 tests. DRF `ValidationError` wrapped into pack-native `ContentPackError`. | [#514](https://github.com/openshiksha/openshiksha/pull/514) | No DB writes; unblocks CP-2. |
| 2026-07-06 | **CP-3 model shipped** (T-3): `ContentSubmission` + `ContentSubmissionState` + `transition_to()` state-machine guard (4 states, idempotent re-approval, reviewer/note/timestamp per transition); migration `0031`; 15 model tests. Model-only — API/materialization/UI still open under CP-3/CP-4. | [#515](https://github.com/openshiksha/openshiksha/pull/515) | One row = one pack (per decided state machine); flagged CP-2's "per question" wording as stale. |
| 2026-07-07 | Grounded CP-2 against the landed model + validator (`content_packs.py` exports `validate_content_pack`/`content_pack_hash`/`ContentPackError`; `ContentSubmission` holds whole-pack `payload`). Fixed CP-2's stale "per question" wording (now one PENDING row per pack). **Decided:** the schema has no stable pack id, so import **never auto-supersedes** — idempotency keys purely on `pack_hash`; `superseded` is a review-time transition only. Queued T-4 (CP-2 import command) + T-5 (CP-3 API + materialization). | — | Queue now T-1 (OSS-1), T-4 (CP-2), T-5 (CP-3 API) open. No external contributors waiting. |
| 2026-07-07 | **CP-2 shipped** (T-4): `import_content_pack <file> [--dry-run]` — validates via CP-1 and stages the whole pack as one `PENDING` `ContentSubmission`, never touching the live bank. Idempotency keyed on `pack_hash` (PENDING/APPROVED re-import is a no-op; REJECTED/SUPERSEDED can be re-staged); never auto-supersedes. 10 tests (accept/dry-run/idempotency/reject paths). | [#517](https://github.com/openshiksha/openshiksha/pull/517) | No new migration; `Question` untouched. Unblocks T-5 (CP-3 API + materialization). |
| 2026-07-07 | **CP-4 shipped** (user-directed session, not a routine run): admin "Content Submissions" page at `/admin/submissions` (`SubmissionsPage` + `useContentSubmissions` hooks, ADMIN-walled route, linked from AdminDashboard). Queue filtered by state (pending default); detail shows the provenance block (author/license/source — what approval publishes with), per-question preview via a pure `packQuestionToPreview` mapper into the **existing `QuestionPreviewPanel`** (zero parallel preview code; defaults mirror the importer's mcq/difficulty-2), and widget-bearing subparts render in the **real `InteractiveWidget` sandbox**. Approve/Reject with note (reject blocks locally without one; the backend requires it too), Reopen for rejected; all legality stays server-side — a 409 from `transition_to()` is surfaced verbatim. 24 new frontend tests (hooks: URL shapes/pagination-unwrap/enabled-gate/409; page: filter default+switch, provenance+preview+sandbox render, approve/reject/reopen flows, note-required, 409 surfaced, approved read-only; mapper: mapping + importer defaults). | (this session) | The preview trusts the payload with no client-side re-validation — CP-1 validated it at import, mirroring how DTB-3 trusted DTB-1/2's contract. Widget preview reuses the same sandboxed `InteractiveWidget` students see, so a reviewer approves exactly what will render. |
| 2026-07-07 | **CP-3 shipped** (T-5): admin-only `ContentSubmissionViewSet` (list/detail + approve/reject/reopen driving `transition_to`) + `content_submissions.py` `materialize_submission()` — approve creates shared-bank `Question` rows (`school=None`, `created_by`=reviewer), idempotent on `pack_hash` via a `content-pack:<hash>` marker tag. Illegal transitions → 409; reject requires a note. 13 API tests (permission walls + materialize + idempotent re-approve). Stacked on #517. | [#518](https://github.com/openshiksha/openshiksha/pull/518) | **Discrepancy:** `Question` has no attribution column → attribution carried by `created_by` + the marker tag → `ContentSubmission.provenance`; first-class attribution field deferred to a future migration. CP-4 (review UI) is the next Track-B step. |
