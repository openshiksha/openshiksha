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

| ID | Increment | Status |
|----|-----------|--------|
| CP-1 | **Content-pack schema** (the keystone): versioned JSON schema for a pack of questions/subparts (incl. `widget_kind`/`widget_config`, reusing the vendored widget schemas + `validate_widget_config`) + provenance block (author, source, license). Pure validator `backend/openshiksha/apps/core/content_packs.py` + schema `…/apps/core/data/content_pack.schema.json` + tests (valid/invalid per field class). No DB writes yet. | ⬜ |
| CP-2 | **`manage.py import_content_pack <file> [--dry-run]`**: validates via CP-1, stages each question as a **`ContentSubmission`** row (Question has **no** status field — see grounding note; don't overload `is_active`, which is soft-delete), never active; idempotent by pack hash; report output. Tests: dry-run, import, re-import no-dupe, invalid rejected. | ⬜ |
| CP-3 | **Submission review model + API**: `ContentSubmission` (pack metadata, state machine pending→approved/rejected, reviewer, notes) with admin-only endpoints; approving materializes the pack's questions into the bank (`school=null` shared bank, `created_by`=reviewer, attribution from the provenance block); rejecting archives with a reason. Mirror the existing `TeacherWidgetVisibility.PENDING_REVIEW` moderation precedent (`models.py:1133`). Tests incl. permission walls. | ⬜ |
| CP-4 | **Review UI (admin)**: a "Submissions" queue page — pack summary, per-question preview (reusing the existing QuestionPreviewPanel/widget sandbox preview), Approve/Reject with note. The maintainer's one-click approval surface. | ⬜ |
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
- [ ] **T-2 (2026-07-05):** CP-1 content-pack schema + pure validator + tests
      (`backend/openshiksha/apps/core/content_packs.py`,
      `backend/openshiksha/apps/core/data/content_pack.schema.json`). Reuse
      `validate_widget_config` (widgets.py:105) for widget-bearing subparts —
      note it raises DRF `ValidationError`; decide whether to wrap. No DB writes.
- [ ] **T-3 (2026-07-06):** CP-3 `ContentSubmission` model only (no API/UI yet) —
      fields per the state machine above (`pack_hash`, `provenance` JSON,
      `state`, `reviewer` FK, `note`, timestamps); migration + model tests for
      the legal/illegal transitions. Mirror `TeacherWidgetVisibility` for the
      state `TextChoices`. Cheap, low-risk table that unblocks CP-2/CP-4.

## Progress ledger

| Date | Increment | PR | Notes |
|------|-----------|----|----|
| 2026-07-05 | Initiative opened (post-launch-video pivot). Tracks A+B scoped; T-1/T-2 queued. | — | Launch video shipped 2026-07-05 (`launch-video-final3`, local-only asset); routines repurposed from the launch track to this initiative. |
| 2026-07-06 | Grounded CP-1/2/3 against code (real paths `backend/openshiksha/apps/core/…`; `validate_widget_config` raises DRF error; Question has no status field; `TeacherWidgetVisibility.PENDING_REVIEW` precedent). Decided CP-3 state machine (4 states). Queued T-3 (ContentSubmission model). | — | No external contributors waiting; execute has not yet started T-1/T-2. |
