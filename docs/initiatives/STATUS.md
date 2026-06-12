# Initiatives - Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short - one row per initiative.

**Last updated:** 2026-06-11 (night) — **Language Access first batch LA-1..5
shipped** across [#308](https://github.com/openshiksha/openshiksha/pull/308)–[#312](https://github.com/openshiksha/openshiksha/pull/312)
(+ LA-5b): in-house i18n module + EN|हिं switcher (no i18next — perf budget
defended, entry ~104 kB of 160), durable `User.preferred_language` with the
device > profile > en precedence contract, the student core loop + parent
dashboard + the whole public surface (home, login, registration) in Hindi,
AI explanations + parent summaries generating in the reader's language
(regenerate-in-place on language switch), and a runtime key-parity guard
(key sets + `{var}` placeholder drift). Home page added to LA-5 scope per
user request. Next: **LA-6** (teacher chrome), **LA-7** (localized emails).

Earlier (2026-06-11 evening) — **Language Access (i18n en/हिंदी)
promoted as the new top initiative**
([doc](2026-language-access.md), [plan](../daily-plans/2026-06-11-plan.md)).
The board had no active bet after ASA closed this morning. Rationale: the
en/hi toggle is the **last open ROADMAP item**, the backend LLM layer already
accepts `language="hi"` on explanations + parent summaries (shipped dark —
same lesson as ASA), and language access is mission-core for a K-12 platform
in India. Other seeds deferred: `/ai/predictions/` surface is an explicit
product call, Widget Studio needs product discovery, the AI-tutor branch is a
5k-line rebase (not atomic). First batch **LA-1..5**: i18n foundation +
switcher (no new dependency — perf budget defended), `User.preferred_language`
+ profile sync, student core-loop chrome in Hindi, AI content in the reader's
language, key-parity CI guard + glossary + parent/auth chrome.

Earlier (2026-06-11 morning) — **AI Surface Activation closed — North Star
reached** ([#299](https://github.com/openshiksha/openshiksha/pull/299)–[#303](https://github.com/openshiksha/openshiksha/pull/303)).
The closing batch lit the **last dark `/ai/` endpoint group**: teachers get an
open-response **AI grading queue** at `/teacher/grading` (#301 — AI suggests a
score/feedback/criterion breakdown, the teacher finalises every grade) plus
inline **rubric authoring + record-response** (#302, first `/ai/open-rubrics/`
consumer, with a teacher-only room-roster API). The provenance vocabulary is
unified behind a shared **`AIBadge`** primitive (#300), #294's orphaned
WeeklyReportPanel polish was re-landed (#299 — stacked-PR process lesson in
the ledger), and the close (#303) added the repeatable
[endpoint-consumer map](../ai-features/endpoint-consumer-map.md) + DoD audit:
**17 `/ai/` endpoints directly consumed, 4 indirect by design, 1 documented
API-only** (`/ai/predictions/`, future product call). `useAsyncGeneration`
extraction carried to maintenance. **Every active initiative is now Done or
Paused — no unblocked next bet on the board until a new initiative is
promoted.** Candidate seeds: an `/ai/predictions/` teacher surface, or the
deferred Widget Studio discovery.

Earlier (2026-06-10) — ASA batch 2 shipped
([#293](https://github.com/openshiksha/openshiksha/pull/293)–[#297](https://github.com/openshiksha/openshiksha/pull/297)):
AI-drafted assignments panel (ASA-6), drill-result explanations (ASA-8),
server-side SM-2 same-day guard (ASA-9), and the error-as-empty-state sweep
across the teacher AI panels.

Earlier (2026-06-09 evening) — **ASA first batch shipped: ASA-1..5
across [#285](https://github.com/openshiksha/openshiksha/pull/285)–[#289](https://github.com/openshiksha/openshiksha/pull/289).**
Students now get post-submit AI answer explanations (first `/ai/explanations/`
consumer, #288); teachers get class misconception clusters (first
`/ai/misconception-clusters/` consumer, #289); recommendation rows click
through to chapter practice (#286); `DueForReviewPanel` got the
skeleton/empty-state pattern (#285); and the SRS drill can no longer
double-run SM-2 in one sitting (#287). **2 of the 4 dark endpoint groups are
now lit** — ASA-6 (assignment drafts) and ASA-7 (open-response grading) are
the remaining ones, each a batch-anchor for a future run.

Earlier same day — **AI Surface Activation promoted as top initiative.** The
2026-06-09 AI-surfaces audit ([polish-backlog](../ai-features/polish-backlog.md))
found four shipped, tested `/ai/` endpoint groups with **zero frontend
consumers** (explanations, misconception-clusters, assignment-drafts,
open-response rubrics/grades) plus inert/inconsistent edges on live AI panels.
First batch (ASA-1..5) planned in
[2026-06-09-plan.md](../daily-plans/2026-06-09-plan.md).

Earlier same day — **Authoring Integrity & Versioning closed —
North Star reached.** Phase 3 shipped across
[#279](https://github.com/openshiksha/openshiksha/pull/279)–[#281](https://github.com/openshiksha/openshiksha/pull/281):
**AIV-6** (guarded re-sync: blast-radius preview → atomic snapshot swap +
selective re-grade → undo from history),
**AIV-7** (`ProblemSetVersion` deduplicated immutable content versions;
assignments pin a version FK; idempotent dedup backfill of every legacy
snapshot), **AIV-8** (version history list + structured diff between any two
versions, surfaced on a new versions page deep-linked from the preview).
Combined with Phase 1 (AIV-1..3, [#270](https://github.com/openshiksha/openshiksha/pull/270)–[#274](https://github.com/openshiksha/openshiksha/pull/274))
and Phase 2 (AIV-4/5, [#276](https://github.com/openshiksha/openshiksha/pull/276)–[#277](https://github.com/openshiksha/openshiksha/pull/277))
the initiative's full DoD is met. Teacher Workspace closed 2026-06-09 with
TW-2 (editable preview, also #276). **Every active initiative is now Done or
Paused** — no unblocked next bet on the board until a new initiative is
promoted.
Earlier (2026-06-07): all unblocked TW increments shipped across **#250, #261–#266**
(TW-1, TW-5, TW-4, TW-3a, TW-3b, TW-6, TW-7); the planned **TW-T** Playwright smoke
was dropped (seams already covered by Vitest + pytest). Earlier batch:
**Performance Budget done** (PERF-01..04 + PERF-06
in [#251](https://github.com/openshiksha/openshiksha/pull/251)–[#255](https://github.com/openshiksha/openshiksha/pull/255);
[#256](https://github.com/openshiksha/openshiksha/pull/256) for the DOMPurify
barrel-export leak). Entry chunk **855 → 93 kB / 247 → 29 kB gzip**, CI guard
at 160 kB defends the cut.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [Language Access — i18n en/हिंदी](2026-language-access.md) | **Active** | **First batch LA-1..5 shipped 2026-06-11** ([#308](https://github.com/openshiksha/openshiksha/pull/308)–[#312](https://github.com/openshiksha/openshiksha/pull/312) + LA-5b): i18n module + EN\|हिं switcher, `preferred_language` end-to-end, student core loop + parent dashboard + full public surface (home/login/registration) in Hindi, AI content in the reader's language, runtime key-parity guard. Devanagari verified in-browser (Noto Sans Devanagari behind Inter/Fraunces). | **LA-6** — teacher surfaces chrome; then LA-7 localized emails |
| - | [AI Surface Activation](ai-surface-activation.md) | Done | **Closed 2026-06-11 — North Star reached.** ASA-1..9 shipped across [#285](https://github.com/openshiksha/openshiksha/pull/285)–[#289](https://github.com/openshiksha/openshiksha/pull/289), [#293](https://github.com/openshiksha/openshiksha/pull/293)–[#302](https://github.com/openshiksha/openshiksha/pull/302): all four dark `/ai/` endpoint groups lit (explanations, misconception clusters, assignment drafts, open-response grading), error-as-empty-state sweep complete, shared `AIBadge` provenance, server-side SRS guard. Close ([#303](https://github.com/openshiksha/openshiksha/pull/303)): [endpoint-consumer map](../ai-features/endpoint-consumer-map.md) + DoD audit — 17 endpoints directly consumed, 4 indirect by design, 1 API-only (`/ai/predictions/`). | `useAsyncGeneration` refactor carried to maintenance; `/ai/predictions/` surface is a future product call |
| - | [Authoring Integrity & Versioning](authoring-integrity-versioning.md) | Done | **All three phases shipped 2026-06-08/09.** Phase 1 (AIV-1..3, [#270](https://github.com/openshiksha/openshiksha/pull/270)–[#274](https://github.com/openshiksha/openshiksha/pull/274)): snapshot foundation + grader/student readers + edit-safety UI. Phase 2 (AIV-4/5, [#276](https://github.com/openshiksha/openshiksha/pull/276)–[#277](https://github.com/openshiksha/openshiksha/pull/277)): editable preview + drift surface. Phase 3 (AIV-6/7/8, [#279](https://github.com/openshiksha/openshiksha/pull/279)–[#281](https://github.com/openshiksha/openshiksha/pull/281)): guarded re-sync + `ProblemSetVersion` dedup + version history & diff UI. DoD met end-to-end. | - |
| - | [Teacher Workspace](teacher-workspace.md) | Done | Closed 2026-06-09 with **TW-2** (editable preview) shipped in [#276](https://github.com/openshiksha/openshiksha/pull/276). Earlier increments: TW-1, TW-3a/b, TW-4, TW-5, TW-6, TW-7 closed 2026-06-07 across [#250](https://github.com/openshiksha/openshiksha/pull/250), [#261](https://github.com/openshiksha/openshiksha/pull/261)–[#266](https://github.com/openshiksha/openshiksha/pull/266). | - |
| - | [Performance Budget](performance-budget.md) | Done | Closed 2026-06-07. PERF-01..04 + PERF-06 shipped in one batch ([#251](https://github.com/openshiksha/openshiksha/pull/251)–[#255](https://github.com/openshiksha/openshiksha/pull/255)); follow-up ([#256](https://github.com/openshiksha/openshiksha/pull/256)) dropped `ReactQueryDevtools` in prod, added a measurement harness, and fixed a `@/shared/ui` barrel-export leak that was dragging DOMPurify into the entry chunk. Entry chunk **855 → 93 kB / 247 → 29 kB gzip** (88% gzip drop); vendor split, route-level `React.lazy`, lazy KaTeX behind `<RichContent>`, CI budget guard at 160 kB. Measured `/login` FCP under Slow 4G + 4× CPU: 4.4 s. | - |
| - | [Interactive Widgets Framework](interactive-widgets-framework.md) | Paused | Tier 1 **Configure** is usable (`WidgetGalleryPanel` + registry schemas). Tier 3 **Code** is usable (`defineWidget`, `npm run widget:new`, `npm run widget:dev -- <kind>`, `/widgets/dev`, docs). First-party library currently includes `_hello`, `thermo-piston`, `number-line`, `function-plotter`, `fraction-bar`, plus admin-only `custom-html`; all render through the same sandboxed iframe and answer-producing widgets report through the shared protocol. | Defer **IW-9 - IW-11** until product discovery proves Widget Studio is more valuable than more first-party/developer-authored widgets. |
| - | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | Done | M1-M7 are closed for the current scope. Mobile shell now has role-aware bottom tabs, account drawer, safe-area/dynamic-viewport padding, large touch targets, responsive surface audit, and focused a11y baseline. Legacy parity gaps are closed or explicitly skipped. Only optional activation remains: run the [seed-visual-baselines](../../.github/workflows/seed-visual-baselines.yaml) workflow once for M6-03 baselines. | - |
| - | [Cabinet Data Fidelity](cabinet-data-fidelity.md) | Done | Closing batch shipped (M7-08, M7-06, M7-03a/b, fidelity-audit guard) + proper taxonomy names baked into the importer. `audit_cabinet_fidelity --strict` is **green on the real 646-question corpus**. M7-11 sandbox primitive shipped and now seeds the new **Interactive Widgets Framework** initiative. | - |

## Legend

- **Active** - being advanced now; pull its top increment.
- **Paused** - intentionally on hold (reason in the doc).
- **Proposed** - written up but not yet started.
- **Done** - North Star reached; keep for history.

## Backlog of future initiatives (proposed, not yet scoped)

These are candidate long-horizon goals. Promote one to its own doc when it
becomes the right next bet.

- **Mobile shell** - bottom tab bar shipped 2026-06-04 (#195 / `M5-01`).
  Remaining work for a proper proposal: route-level mobile layouts, PWA
  install, offline-tolerant question viewing.
- **AI tutor surface** - student-facing conversational help over the existing
  hint + explanation backends. A branch (`ai/2026-06-04-ai-tutor-chat`,
  commit `1e3c50f9`) has a Socratic chat coded but diverged ~5 000 lines from
  `modernization`. Promotion = rebase, harden, formalise.
- **Accessibility pass** - WCAG 2.1 AA across the migrated V2 surfaces. A
  focused baseline pass landed 2026-06-04 (M6-01 #202) - skip link, dialog
  semantics, image alts. Promote to its own initiative when ready for a
  full audit (keyboard walkthrough, screen-reader spot-check, axe-core CI).
- **[Authoring Integrity & Versioning](authoring-integrity-versioning.md)** -
  ⚪ Proposed (2026-06-07). Editing a problem set / question today retroactively
  changes already-assigned and already-graded work, because `grade_submission`
  reads the **live** set + correct answers. Phase 1 (per-assignment content
  snapshot) removes that silent-corruption risk and unblocks an **editable**
  teacher preview; later phases add versioning + a guarded re-sync. Motivated by
  the editable-preview ask on [#248](https://github.com/openshiksha/openshiksha/pull/248).
- _(Promoted 2026-06-07 → [Performance Budget](performance-budget.md), now the
  active top initiative.)_
