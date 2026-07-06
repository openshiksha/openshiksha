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

| ID | Increment | Status |
|----|-----------|--------|
| CP-1 | **Content-pack schema** (the keystone): versioned JSON schema for a pack of questions/subparts (incl. `widget_kind`/`widget_config`, reusing the vendored widget schemas + `validate_widget_config`) + provenance block (author, source, license). Pure validator `apps/core/content_packs.py` + tests (valid/invalid per field class). No DB writes yet. | ⬜ |
| CP-2 | **`manage.py import_content_pack <file> [--dry-run]`**: validates via CP-1, imports questions as **`status=pending_review`** (new field/flag on Question or a ContentSubmission model), never active; idempotent by pack hash; report output. Tests: dry-run, import, re-import no-dupe, invalid rejected. | ⬜ |
| CP-3 | **Submission review model + API**: `ContentSubmission` (pack metadata, state machine pending→approved/rejected, reviewer, notes) with admin-only endpoints; approving activates the pack's questions into the bank with attribution; rejecting archives with a reason. Tests incl. permission walls. | ⬜ |
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
      (`apps/core/content_packs.py`, `apps/core/data/content_pack.schema.json`).
      Reuse `validate_widget_config` for widget-bearing subparts. No DB writes.

## Progress ledger

| Date | Increment | PR | Notes |
|------|-----------|----|----|
| 2026-07-05 | Initiative opened (post-launch-video pivot). Tracks A+B scoped; T-1/T-2 queued. | — | Launch video shipped 2026-07-05 (`launch-video-final3`, local-only asset); routines repurposed from the launch track to this initiative. |
