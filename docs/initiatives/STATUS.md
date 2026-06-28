# Initiatives - Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short - one row per initiative.

> **🔒 Routine ownership fence.** [AI-Native Interactive Learning](ai-native-interactive-learning.md)
> is built **exclusively** by the `openshiksha-ai-features` routine. The
> `openshiksha-plan`, `openshiksha-execute`, and `openshiksha-dependabot`
> routines **MUST NOT** plan, select, or build any of its increments — even if
> it is the only thing with open work. It is intentionally **omitted from the
> priority table below** so it is never picked as the "top active initiative."

**Last updated:** 2026-06-25 (latest) — **NEW TOP INITIATIVE PROMOTED:
[Production Observability & Operational Readiness](2026-production-observability.md).**
With Accessibility closed (below) the priority board carried **no unblocked next
bet** — OSS Readiness, Mobile Shell, and Language Access are Done; Interactive
Widgets is Paused; LA-10 is blocked on product design; AI-Native is fenced to the
`ai-features` routine. Meanwhile OpenShiksha is **live in production** (DO
droplet, k3s, `openshiksha.org`) and effectively **un-observable**: no error
tracking, the k8s **readinessProbe probes the cheap `/healthz/`** (never checks
DB/cache, so a pod with a dead DB still gets traffic) even though `/api/v1/health/`
*does* the deep check and the `healthz` docstring itself asks for the missing
`/readyz`; logs are unstructured + uncorrelated; the shared `ErrorBoundary`
reports nowhere. The 2026-06-25 planning run promotes **Production Observability**
— general foundation-hardening in the plan/execute lane, decomposing into atomic,
low-risk, **env-gated** PRs. **Batch 1 (OBS-1..5)** planned in
[2026-06-25-plan.md](../daily-plans/2026-06-25-plan.md): `/readyz/` deep probe +
readinessProbe repoint (OBS-1) → `/api/v1/version/` build-info (OBS-2) →
env-gated backend Sentry + secret scrubber (OBS-3) → request-correlation id +
JSON log option (OBS-4) → env-gated frontend error reporting via the existing
`ErrorBoundary` (OBS-5). Everything is additive: no DSN / no `LOG_FORMAT=json` ⇒
behaviour is byte-for-byte today's. The `ai-features` routine fence is respected.
*(Prior update below.)*

**Last updated:** 2026-06-25 — **Accessibility — WCAG 2.1 AA INITIATIVE
CLOSED ✅ (all six DoD items met).** Batch 4 landed the keyboard sign-off and
closed the initiative. **A11Y-16** repaired two rows the Batch-3 close-out
mis-baselined: `/teacher/questions/new` and `/parent/insights` were gated but not
actually clean — `CreateQuestionPage` uses **raw `<select>`** (not the shared
labelled `Select`), so it carried 4 `select-name` criticals + 1 `brand-700`-on-tint
contrast node, and the single-child insights *landing* redirected to the child
detail, tripping the deep-link URL guard. Fixed with aria-labels +
`brand-700 → brand-800`, and the landing is now audited with two children
(`parentMultiChild`) so it renders its own picker. **A11Y-18** flips the initiative
**Status → Closed**: DoD item 5 is met — the keyboard half is automated + gated
(`e2e/keyboard.spec.ts`: skip-link bypass, focus order, focus-visible), and the
human NVDA/VoiceOver listen-through is **formally waived by the project owner** (no
screen-reader tester available), with axe name/role/label gating + the
announce-region inventory standing in. The journey tables in
`a11y/screen-reader-signoff.md` are left **unticked, not claimed as passed**. One
explicit fast-follow remains in the backlog (not blocking close): a true focus
**trap + restore** on the QuestionBank "Add to set" side-sheet. The `ai-features`
routine fence is respected. *(Prior update below.)*

**Last updated:** 2026-06-24 — **Accessibility Batch 3 FULLY CLOSED —
authoring forms + parent insights measured & gated (DoD item 6 ✅).** A11Y-13/15
added the last unmeasured authenticated surfaces to the harness —
`/teacher/questions/new`, `/teacher/assignments/new`, `/teacher/problem-sets/new`,
`/parent/insights`, `/parent/insights/:childId`. The baseline came back
`blocking === []` on all five: the dense authoring forms compose from the shared
labelled `Input`/`Select`/`Textarea` primitives, so the anticipated A11Y-14
labelling/heading remediation was a no-op and the rows gate directly. The same PR
fixes a previously-uncovered crash — the dashboard's `ClassroomCodeWidget` reads
the bare-array `/users/me/classroom-code/` endpoint, which the harness catch-all
mishandled; now stubbed (and the widget is exercised by the gated teacher-dashboard
route). **DoD item 6 fully met.** **Next: Batch 4 — automated keyboard-traversal
spec + screen-reader (NVDA/VoiceOver) sign-off** (DoD item 5). The
`ai-features` routine fence is respected. *(Prior update below.)*

**2026-06-23** — **Accessibility Batch 3 (core) CLOSED — teacher +
parent core surfaces measured, remediated & gated.** Building on the same-day
Batch 2 close-out, Batch 3 generalized the authenticated axe harness to the
teacher and parent roles and extended the gated AA contract to those surfaces:
A11Y-9 ([#442](https://github.com/openshiksha/openshiksha/pull/442) — role-parametrized
`e2e/support/auth.ts` + `/teacher`, `/teacher/questions`, `/teacher/grading`,
`/parent` baselined; teacher surfaces clean) → A11Y-11
([#450](https://github.com/openshiksha/openshiksha/pull/450) — the one finding:
small `brand-700` text on the `brand-50` tint = 4.45 : 1 → `brand-800`, the
`/parent` link + `AssignmentList` badge, rule documented) → **A11Y-12**
([#451](https://github.com/openshiksha/openshiksha/pull/451)) flips all four
teacher/parent routes to `gate: true` (all `blocking === []`) +
Batch 3 close-out (change doc, teacher/parent manual checklist, ledger). The
`ai-features` routine fence is respected. *(Prior update below.)*

**2026-06-23** — **Accessibility Batch 2 CLOSED — student
core loop measured, remediated & gated.** The batch shipped across A11Y-4
([#417](https://github.com/openshiksha/openshiksha/pull/417) — brand-shade decision:
`brand-700 → #C05300`, `.btn-brand` repainted ≥ 4.5 : 1, `/` gated) → A11Y-FV
([#418](https://github.com/openshiksha/openshiksha/pull/418) — keyboard
focus-visible ring on the shared primitives) → A11Y-6
([#419](https://github.com/openshiksha/openshiksha/pull/419) — authenticated axe
harness `e2e/support/auth.ts` + student core-loop baseline, **structurally clean**)
→ A11Y-7 ([#420](https://github.com/openshiksha/openshiksha/pull/420) — `StreakBadge`
contrast, the one blocking finding) → **A11Y-8 (this PR)** flips `/student`,
`/student/assignments/:id`, `/student/proficiency`, `/student/srs-drill/:entryId`
to `gate: true` (all `blocking === []`) + Batch 2 close-out (change doc, student-loop
manual checklist, ledger). **DoD item 4 (student core loop remediated + gated) is
done.** The measured-and-enforced AA contract now covers the public front door
*and* the student core loop. **Next: Batch 3 — teacher/parent surfaces** (reuse the
A11Y-6 authenticated harness: baseline → remediate → gate). The `ai-features`
routine fence is respected. *(Prior update below.)*

**2026-06-22** — **Open-Source Readiness CLOSED — DoD met.**
The closing batch shipped: OSS-6 (`.github/` issue + PR templates,
[#432](https://github.com/openshiksha/openshiksha/pull/432)) → OSS-9 (README
product screenshots, [#433](https://github.com/openshiksha/openshiksha/pull/433))
→ OSS-8 (ASCII → GitHub-rendered Mermaid architecture diagram,
[#434](https://github.com/openshiksha/openshiksha/pull/434)) → OSS-7 (root dev
guides consolidated under `docs/dev/` + index, links repointed,
[#435](https://github.com/openshiksha/openshiksha/pull/435)) → OSS-10 (repo
metadata via `gh repo edit` + auto-detected MPL-2.0 license badged, this PR).
A clean-checkout newcomer can now understand, run, and contribute from the README
+ linked docs alone. **Accessibility (Priority 2, Batch 2 already planned
2026-06-20) is now the top active initiative.** The `ai-features` routine fence
is respected. *(Prior update below.)*

**2026-06-21** — **Open-Source Readiness promoted to
Priority 1 (Active).** With the modern stack live in production, the focus is
making the repo public-ready: Batch 1 (OSS-1..5, [#425](https://github.com/openshiksha/openshiksha/pull/425))
archived the retired Django 1.11 monolith under `legacy/`, cleaned root cruft,
rewrote the README around the real CI/CD pipeline + branch→env model, and added
the standard OSS files (CONTRIBUTING / SECURITY / CODE_OF_CONDUCT). Remaining:
issue/PR templates, docs consolidation, architecture diagram, screenshots.
Accessibility (WCAG 2.1 AA) remains Active at Priority 2. *(Prior update below.)*

**2026-06-19** — **Accessibility — WCAG 2.1 AA promoted
AND Batch 1 shipped.** A11Y-1 ([#389](https://github.com/openshiksha/openshiksha/pull/389),
per-route axe baseline + initiative doc), A11Y-2
([#390](https://github.com/openshiksha/openshiksha/pull/390),
`eslint-plugin-jsx-a11y` static gate, 11 hits fixed), and A11Y-5 (record axe
`incomplete`; **gate** `/login`, `/register`, `/register/school`,
`/register/open`, `/enquire`; change doc + manual checklist). **The batch found
the public surfaces already structurally clean** — A11Y-3 (label/landmark/heading)
needed no remediation, and the contrast story is **one systemic finding**:
`.btn-brand` (white on `#FF6F00`, ≈ 2.8 : 1) fails AA in its enabled state. So
**A11Y-4 is deferred** — repainting the sole brand anchor across every screen is a
**design-shade decision**, not a mechanical fix (the auth CTAs render disabled at
load so axe never flags them; the `/` hero failure lands in `incomplete`). The
next batch needs that brand-shade call, then a token-usage sweep + gating `/` and
the student core-loop surfaces. *(Original promotion rationale follows.)* With
Mobile Shell & PWA-Offline complete and the
board carrying no unblocked next bet, the 2026-06-19 planning run promotes the
backlog's **accessibility audit** candidate — the only named next bet that is both
unblocked and decomposes into atomic, low-risk, frontend-only PRs (AI-tutor is a
~5k-line non-atomic rebase; `/ai/predictions/` is a deferred product call). The
runway already exists: `@axe-core/playwright` + `axe-core` devDeps, an
`e2e/a11y.spec.ts` axe spec (reporting-mode, `/design` only), and a CI `frontend-e2e`
job that runs it and uploads the report; M6-01 (#202) shipped a focused baseline and
**explicitly deferred** the full audit "for a dedicated a11y initiative." **Batch 1
(A11Y-1..5)** planned in [2026-06-19-plan.md](../daily-plans/2026-06-19-plan.md):
per-route axe baseline across the public surfaces → `eslint-plugin-jsx-a11y` static
gate → structural (label/landmark/heading) + colour-contrast remediation → **flip the
axe gate** (`FAIL_ON_BLOCKING = true`) for the cleaned routes so the gain can't
regress. Initiative doc `2026-accessibility-wcag-aa.md` is created in A11Y-1. The
`ai-features` routine fence is respected (AI-Native Interactive Learning untouched).

**Earlier (2026-06-18)** — **Mobile Shell & PWA-Offline — Batch 4
(RML-1..5) SHIPPED: route-level mobile layouts — INITIATIVE COMPLETE**
([plan](../daily-plans/2026-06-18-plan.md), [#382](https://github.com/openshiksha/openshiksha/pull/382)–[#385](https://github.com/openshiksha/openshiksha/pull/385)).
The dense teacher surfaces that still overflowed horizontally on a phone are now
readable at 360 px: a reusable `shared/ui/ResponsiveTable` primitive (real `<table>`
at `sm:`+, stacked label/value cards below — repo `hidden sm:table`/`sm:hidden`
dual-render, no `matchMedia`) — first consumer ClassHealthPanel (RML-1, #382) →
assignment-detail submissions table → cards, plus the page localized back into the
LA registry (it had slipped LA-6) (RML-2, #383) → CreateQuestionPage fixed grids →
mobile-first `grid-cols-1 sm:grid-cols-*` + 44 px tab targets (RML-3, #384) →
OpenResponseGradingPage review form stacks `flex-col sm:flex-row` + `break-words`
(RML-4, #385). Frontend-only, entry chunk unchanged. **With both later phases (web
push, route-level layouts) and the first-phase DoD done, the Mobile Shell &
PWA-Offline initiative is COMPLETE.** No unblocked next bet — the next planning run
promotes a fresh top initiative (candidates below).

**Earlier (2026-06-17)** — **Mobile Shell & PWA-Offline — Batch 3
(MPN-1..5) SHIPPED: web push due-date reminders**
([plan](../daily-plans/2026-06-17-plan.md), [#375](https://github.com/openshiksha/openshiksha/pull/375)–[#379](https://github.com/openshiksha/openshiksha/pull/379)).
The **mobile-native notification channel**: `PushSubscription` model + VAPID +
`pywebpush` (MPN-1) → subscribe/unsubscribe API + `send_web_push` (MPN-2) →
`public/push-handler.js` on the MSO-3 SW (MPN-3) → `usePushSubscription` hook +
opt-in banner + ProfilePage toggle (MPN-4) → web push fanned from
`send_due_date_reminders` (MPN-5). Email stays source of truth; push is additive.

**Earlier (2026-06-15)** — **Mobile Shell & PWA-Offline — Batch 2
(MSO-6..10) SHIPPED: offline *write*-tolerance**
([plan](../daily-plans/2026-06-15-plan.md)). Batch 1 made the student core loop
survive offline for *reads*; Batch 2 now queues and replays assignment auto-saves
and submissions made offline — **exactly once, no double-grade**. Five PRs,
lowest-risk first: **MSO-6** ([#367](https://github.com/openshiksha/openshiksha/pull/367))
replay-safe/idempotent submission writes server-side (closed a latent re-grade
hazard in the grading `post_save` signal) → **MSO-7**
([#368](https://github.com/openshiksha/openshiksha/pull/368)) durable offline
mutation queue (paused-mutation persist allowlist + keyed `setMutationDefaults` +
`networkMode: 'offlineFirst'` + `resumePausedMutations` on reconnect — no new dep)
→ **MSO-8** ([#369](https://github.com/openshiksha/openshiksha/pull/369)) "Saved
offline · will sync" status UX → **MSO-9**
([#370](https://github.com/openshiksha/openshiksha/pull/370)) offline final-submit
(optimistic + score reconcile on replay) → **MSO-10** close-out. No new runtime
dependency; rode Batch 1's persister + `useOnlineStatus` + LA i18n. **Next phases:**
route-level mobile layouts (dense teacher tables); web push for due-date reminders.

**Earlier (2026-06-14)** — **Mobile Shell & PWA-Offline — Batch 1
(MSO-1..5) shipped** ([doc](2026-mobile-shell-pwa-offline.md),
[plan](../daily-plans/2026-06-14-plan.md)): OpenShiksha is now an installable PWA
(manifest + maskable icons #358, `vite-plugin-pwa` service worker #360) whose
student core loop survives a flaky/absent connection (persisted React Query cache
#361 + precached shell), with an honest localized offline banner (#359) and an
"Add to home screen" affordance (#362). Next in this initiative: offline
**write**-tolerance (queue + replay submissions on reconnect). The initiative was
promoted today as the new top bet — Language Access closed its North Star
with LA-9 yesterday; only LA-10 (authored-content translation) remains and stays
blocked on product design — so the board's named next bet, **Mobile shell /
PWA-offline**, is now active. The mobile *chrome* already exists (M5-01 bottom
tabs + the V2 safe-area/touch-target pass); what's missing is **installability**
and **offline read-tolerance** — verified greenfield 2026-06-14 (no manifest, no
service worker, no `navigator.onLine` handling, React Query in-memory only).
First batch **MSO-1..5**: web app manifest + maskable icons (MSO-1), network-
status hook + offline banner (MSO-2), `vite-plugin-pwa` service worker (MSO-3),
React Query → IndexedDB persistence so loaded assignments read offline (MSO-4),
and a `beforeinstallprompt` install affordance + close-out (MSO-5). The whole
batch rides the existing perf-budget discipline (SW + persister live outside the
~41 kB-gzip entry chunk) and localizes through the LA i18n framework for free.

Earlier (2026-06-13) — **LA-9 shipped — the third language
(Marathi) pilot proves the framework; only LA-10 (blocked on product design)
remains.** LA-9a generalized the binary `en|hi` machine into a single
`locales/registry.ts` + a complete-vs-pilot parity contract
([#349](https://github.com/openshiksha/openshiksha/pull/349), zero behavior
change for en/hi), then Marathi (मरा) rolled out as **pure content**: anonymous
journey ([#350](https://github.com/openshiksha/openshiksha/pull/350)), student
core loop ([#351](https://github.com/openshiksha/openshiksha/pull/351)), parent
dashboard + a backend `resolve_ai_language()` mr→en fallback guard
([#352](https://github.com/openshiksha/openshiksha/pull/352)), and a
coverage-report test + glossary + close-out
([#353](https://github.com/openshiksha/openshiksha/pull/353)). The whole
engineering surface for language #3 was one registry entry + a union widening —
the North Star clause ("a third language must be a content task, not an
engineering task") is met. Language #4 (a non-Devanagari stress test like Tamil)
is now config + content + one font-stack entry, no code change. **Next: only
LA-10** (authored-content/question translation) remains and stays **blocked on
product design** — do not start without promotion. With Language Access
effectively complete, **Mobile shell / PWA-offline** is the strongest
next-initiative seed. **Lesson:** stacking each locale PR on the prior (9a→9b→9c
→9d→9e) avoided the merge-anchor collisions the 6e parallel PRs hit; and a
pre-commit black reformat can fail the first `git commit` silently — re-stage
and re-commit, don't push assuming it landed.

Earlier (2026-06-13) — **LA-6 batch 6a–6d shipped**
([#318](https://github.com/openshiksha/openshiksha/pull/318)–[#321](https://github.com/openshiksha/openshiksha/pull/321)):
**6a** teacher dashboard + 8 insight panels, **6b** create-assignment, **6c**
build-problem-set, **6d** AI grading queue. ~270 keys, plural via `*One`/`*Many`
pairs, rich sentences recomposed as whole interpolations.

Earlier (2026-06-13) — **LA-7 localized emails shipped**
([#314](https://github.com/openshiksha/openshiksha/pull/314)): all four
transactional emails render in the recipient's `preferred_language` (+ fixed the
Monday parent-summary batch that never passed a language).

Earlier (2026-06-11 night) — **Language Access first batch LA-1..5
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
| 1 | [Production Observability & Operational Readiness](2026-production-observability.md) | **Active** | **Promoted 2026-06-25**; **Batch 1 (OBS-1..5) SHIPPED 2026-06-25** ([#460](https://github.com/openshiksha/openshiksha/pull/460)–[#464](https://github.com/openshiksha/openshiksha/pull/464)): `/readyz/` deep DB+cache probe + k8s readinessProbe repointed off the cheap `/healthz/` (drain-not-crash); `/api/v1/version/` build-info (git sha/build time baked via CI build-args); env-gated backend Sentry (`SENTRY_DSN`) + secret-scrubbing `before_send`; `RequestIDMiddleware` correlation id threaded through logs + `LOG_FORMAT=json` option; env-gated frontend error reporting (`VITE_SENTRY_DSN`) via the shared `ErrorBoundary` (dynamic import ⇒ entry chunk unchanged). All additive — no DSN / no `LOG_FORMAT=json` ⇒ behaviour byte-for-byte today's. **Batch 2 (MET-1..5) SHIPPED 2026-06-27** ([#467](https://github.com/openshiksha/openshiksha/pull/467)–[#471](https://github.com/openshiksha/openshiksha/pull/471)): gated Prometheus `/metrics` (`METRICS_ENABLED`/`METRICS_TOKEN`, 404 by default; `prometheus-client`, not always-on `django-prometheus`) → on-scrape business/queue-depth gauges (lazy-registered, fault-tolerant) → `TaskResult`-derived Celery health (gated on the `django-db` result backend; honest no-op under Redis) → gated HTTP request count + latency middleware → Grafana starter (`docs/ops/grafana/openshiksha-overview.json`) + scrape runbook (`docs/ops/metrics.md`). All additive — no `METRICS_ENABLED` ⇒ `/metrics` 404s, byte-for-byte today's. **Batch 3 (BAK-1..5) SHIPPED 2026-06-27** ([#474](https://github.com/openshiksha/openshiksha/pull/474)–[#477](https://github.com/openshiksha/openshiksha/pull/477) + docs PR): version-matched `pg_dump`/`pg_restore` scripts + `Dockerfile.backup` (`FROM postgres:15-alpine` + pinned static `mc`) → a *tested* local restore drill asserting row-count parity (`scripts/backup/drill.sh`, non-destructive scratch DB) → a prod-overlay-only nightly `CronJob` (`k8s/overlays/prod/backup-cronjob.yaml`; CI publishes the `openshiksha-backup` image) → a `BackupRun` freshness gauge (`openshiksha_backup_age_seconds`) on the MET-2 collector → `docs/ops/backups.md` runbook. All additive — qa/dev kustomize byte-for-byte unchanged, no secret committed. | **Batch 4 — Uptime & alerting** — external uptime check on `/healthz/` + `/readyz/`; alert routing (email/ntfy) on Sentry error-rate + probe-fail + the Batch-2 metrics + the Batch-3 `openshiksha_backup_age_seconds` freshness gauge. **Follow-ups:** wire `VITE_SENTRY_DSN` into the CI frontend build once a DSN is provisioned; wire `record_backup_run` into the backup script/Job so prod populates the freshness gauge; add a CI smoke that runs `drill.sh` against an ephemeral compose Postgres. |
| - | [Open-Source Readiness](open-source-readiness.md) | **Done** | **DoD met 2026-06-22.** Batch 1 (OSS-1..5, [#425](https://github.com/openshiksha/openshiksha/pull/425)) archived the Django 1.11 monolith under `legacy/`, rewrote the README around the real CI/CD + branch→env model, added `CONTRIBUTING`/`SECURITY`/`CODE_OF_CONDUCT`. **Batch 2/3 (OSS-6..10) shipped 2026-06-22** ([#432](https://github.com/openshiksha/openshiksha/pull/432)–[#435](https://github.com/openshiksha/openshiksha/pull/435) + metadata PR): `.github/` issue+PR templates, README product screenshots, a GitHub-rendered Mermaid architecture diagram, the loose root dev guides consolidated under `docs/dev/` (kebab-cased, history preserved) + index, and repo metadata (description/topics/homepage via `gh repo edit`) with the auto-detected MPL-2.0 license badged. A clean-checkout newcomer can now understand, run, and contribute from the README + linked docs alone. | **Initiative complete.** Accessibility (Priority 1) becomes the top active initiative — Batch 2 already planned in [`2026-06-20-plan.md`](../daily-plans/2026-06-20-plan.md). |
| - | [Accessibility — WCAG 2.1 AA](2026-accessibility-wcag-aa.md) | **Done** | **CLOSED 2026-06-25 — all six DoD items met.** Batch 1 ([#389](https://github.com/openshiksha/openshiksha/pull/389)–[#391](https://github.com/openshiksha/openshiksha/pull/391)): per-route axe baseline + jsx-a11y gate; public/auth surfaces gated. Batch 2 ([#417](https://github.com/openshiksha/openshiksha/pull/417)–[#420](https://github.com/openshiksha/openshiksha/pull/420), [#441](https://github.com/openshiksha/openshiksha/pull/441)): brand-shade decision (`brand-700 → #C05300`), focus-visible pass, authenticated axe harness, student core loop gated. Batch 3 ([#442](https://github.com/openshiksha/openshiksha/pull/442), [#450](https://github.com/openshiksha/openshiksha/pull/450)–[#451](https://github.com/openshiksha/openshiksha/pull/451), A11Y-13/15): teacher/parent core + authoring forms + parent insights gated. **Batch 4** ([#455](https://github.com/openshiksha/openshiksha/pull/455), A11Y-16/18): keyboard gate spec; repaired the two mis-baselined rows (`CreateQuestionPage` raw-`<select>` labels + tint contrast; insights-landing redirect); initiative closed — human NVDA/VoiceOver pass **waived by project owner**, automated coverage standing in. | **Initiative complete.** Backlog fast-follow (non-blocking): focus trap+restore on the QuestionBank "Add to set" side-sheet. |
| - | [Mobile Shell & PWA-Offline](2026-mobile-shell-pwa-offline.md) | **Done** | **Batch 1 (MSO-1..5) shipped 2026-06-14** ([#358](https://github.com/openshiksha/openshiksha/pull/358)–[#362](https://github.com/openshiksha/openshiksha/pull/362)): installable PWA + offline *read*-tolerance. **Batch 2 (MSO-6..10) shipped 2026-06-15** ([#367](https://github.com/openshiksha/openshiksha/pull/367)–[#370](https://github.com/openshiksha/openshiksha/pull/370)): offline *write*-tolerance — queue + replay. **Batch 3 (MPN-1..5) shipped 2026-06-17** ([#375](https://github.com/openshiksha/openshiksha/pull/375)–[#379](https://github.com/openshiksha/openshiksha/pull/379)): web push due-date reminders. **Batch 4 (RML-1..5) shipped 2026-06-18** ([#382](https://github.com/openshiksha/openshiksha/pull/382)–[#385](https://github.com/openshiksha/openshiksha/pull/385)): route-level mobile layouts — `ResponsiveTable` primitive + dense teacher tables/forms → responsive on phones. **First-phase DoD + both later phases done → initiative complete.** | **No unblocked next bet.** The next planning run promotes a fresh top initiative — candidates: **AI-tutor rebase** (`ai/2026-06-04-ai-tutor-chat`, ~5k-line diverged branch), an **`/ai/predictions/` teacher surface**, or an **accessibility audit (WCAG 2.1 AA)**. LA-10 (authored-content translation) stays blocked on product design. |
| 2 | [Language Access — i18n en/हिंदी/मराठी](2026-language-access.md) | **Done-but-for-LA-10 (blocked)** | **LA-1..9 shipped.** Foundation + EN\|हिं switcher, `preferred_language` end-to-end, student/parent/public/teacher surfaces, AI content + emails in the reader's language, `Intl` date/number helper ([#308](https://github.com/openshiksha/openshiksha/pull/308)–[#326](https://github.com/openshiksha/openshiksha/pull/326)). **LA-9 closed 2026-06-13** — N-locale registry + pilot-coverage parity ([#349](https://github.com/openshiksha/openshiksha/pull/349)) then **Marathi (मरा)** as pure content across the anonymous journey, student loop, and parent dashboard + a backend mr→en AI fallback guard ([#350](https://github.com/openshiksha/openshiksha/pull/350)–[#353](https://github.com/openshiksha/openshiksha/pull/353)). The framework now makes a new language config + content, no code change. | **LA-10** (authored-content/question translation) — blocked on product design, do not start without promotion. Then **Mobile shell / PWA-offline** |
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
