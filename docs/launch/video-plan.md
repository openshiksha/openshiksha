# OpenShiksha Launch Video — Plan

> The working document for the launch video. Maintained daily by the
> `openshiksha-plan` routine (script/shots/checklist) and executed by
> `openshiksha-execute` (camera-ready tasks). Raw material:
> [`docs/demo/golden-path.md`](../demo/golden-path.md) — the 12 shipped demo
> beats. Status: **DRAFT v0.1 (seeded 2026-07-01)**.

## The film

**Working title:** *"AI builds the question. It never grades your kid."*

**Length:** ~2:30. **Format:** screen-capture product demo with voiceover,
recorded on the live stack. **Audience:** teachers/parents + the open-source
crowd (Show HN / Product Hunt). **The one idea to land:** every ed-tech demo
shows AI *answering*; OpenShiksha shows AI *authoring* interactive material
while a deterministic engine does all grading — bounded AI you can trust with
children, open source, in three languages, working offline.

## Script v0.1 (timecoded)

| Time | Beat | On screen | Voiceover (draft) |
|---|---|---|---|
| 0:00–0:15 | Hook | Cold open: teacher types *"a number line where students mark 3/4"* → widget materializes in live preview | "Every AI-education demo shows a chatbot answering questions. Watch something different — AI *building* the question." |
| 0:15–0:45 | Describe-to-Build (Beats 2–3) | Gallery → ✨ prompt box → Generate → live sandboxed preview, tweak a field, **Use this widget** | "One plain-English sentence becomes a working, auto-graded manipulative. Schema-validated before it ever renders — malformed AI output can't reach the classroom." |
| 0:45–1:05 | The multiplier (Beat 5) | Tick *"Each student gets different numbers"* → 🎲 pill → split screen: two students, different number lines | "One description, a different problem for every student. Same skill, nothing to copy." |
| 1:05–1:40 | The student + the coach (Beats 7, 9–10) | Student drags the point → graded. Step-solver: `2x + 3 = 7`, type `2x = 10` → instant ✗ → coach auto-fills → "Why is this wrong?" → ✨ explanation | "Correctness is never the AI's call — a deterministic engine checks every step, live, offline. AI only explains the slip *after* the engine caught it." |
| 1:40–2:05 | Trust & reach | Language switcher EN → हिंदी on the student loop; airplane-mode toggle → the assignment keeps working, "Saved offline · will sync"; parent dashboard AI summary | "Works in your language. Works without internet. Parents get a plain-language summary. Built for classrooms in India." |
| 2:05–2:30 | CTA | README / architecture diagram / openshiksha.org / GitHub stars button | "OpenShiksha is open source and live. Link below." |

**Resolved (2026-07-01):** the meta-story ("built by scheduled AI agents")
stays **out** of this cut — it goes to the separate devlog video ([`ideas.md`](ideas.md)
#2) so the product video stays about kids and teachers, not tooling.

**Resolved (2026-07-02):** PV-3 (generate a whole verified practice problem
on-screen) **makes the cut.** The on-screen `PracticeProblemPanel` on
`/widgets/dev` is now built and **in review as [#504]** (feat/ai-native-2026-07-02-pv-3);
it's fenced to the `openshiksha-ai-features` routine, so this stays a *note* — do
not queue it here. Slot it between the multiplier (1:05) and the student loop as
a second "AI proposes, the engine disposes" moment. See shot 11 below; unfence to
shoot only once #504 merges to `qa`.

**Open scripting question:** the language count. The build ships **two** UI
locales in the switcher (EN + हिंदी) — Marathi was removed from the frontend
registry (`coverage.test.ts:23` "Marathi was removed"; backend `preferred_language`
still accepts `mr`). The trust-beat VO was rewritten from "Three languages" to
"Works in your language". Decide before picture lock: (a) restore the Marathi
pilot dictionary (content-only, see T-5) and reinstate the three-language claim,
or (b) ship the two-language cut. Recommendation: (a) — the i18n story is
stronger at three and the model already carries `mr`.

[#504]: https://github.com/openshiksha/openshiksha/pull/504

## Shot list

| # | Shot | Route / setup | Demo beat | Status |
|---|---|---|---|---|
| 1 | Describe-to-Build generate + attach | Create Question → Add interactive widget | Beats 2–3 | ✅ code-verified 2026-07-01 (26 tests: real ✨ + Auto- fallback + transport-error + pending); live-walk still pending. Script caveat: use a step-0.25 0..1 axis and mark **½**, not ¾ (¾=0.75 rounds to 0.8 on that grid) |
| 2 | 🎲 randomized-per-student toggle | Same prompt box, checkbox on | Beat 5 | ⬜ needs two demo student logins |
| 3 | Two students, different numbers | Open question as 2 students, split screen | Beat 4/5 | ⬜ needs seeded students with real names |
| 4 | Student drags point → graded | Assignment detail as student | Beat 3 | ⬜ |
| 5 | Step-solver live ✓/✗ + coach auto-feed | `/widgets/dev?kind=step-solver` (or QuestionCard if landed) | Beats 7, 10 | ✅ code-verified 2026-07-01 (44 tests: live ✓/✗, commit-not-keystroke, bad-step auto-feed + ⚡ flag, correct never feeds). Playground only — coach is not yet in the real `QuestionCard` (golden-path GSV-4 follow-up), so shoot on `/widgets/dev` |
| 6 | ✨ AI explanation of wrong step | Same, "Why is this wrong?" | Beat 9 | ⬜ requires live ANTHROPIC key (must show ✨, not Auto-) |
| 7 | Language switch en→hi | Student dashboard, switcher | LA initiative | ⚠️ drifted 2026-07-02: switcher ships **EN + हिंदी only** — Marathi is not selectable. `registry.ts` `LOCALES` = [en, hi], no `mr` dictionary; `coverage.test.ts:23` "Marathi was removed" (registry+coverage tests green, 9/9). Backend model still accepts `mr`. Script updated to two-language. To restore मराठी on screen see T-5 |
| 8 | Offline: airplane mode mid-assignment | DevTools offline toggle, banner + queued save | MSO initiative | ⬜ rehearse replay-on-reconnect |
| 9 | Parent AI weekly summary | Parent dashboard | ASA initiative | ⬜ needs child with real activity history |
| 10 | B-roll: README, Mermaid diagram, PR history | GitHub | — | ⬜ |
| 11 | PV-3: "Generate a practice problem" → verified problem renders, answer shown | `/widgets/dev` → PracticeProblemPanel | Beat 13 | ⬜ **in review [#504]** — not on `qa` yet; 33 PV-3 tests green on the branch (hook 7, panel 19-ish, dev-page). Fenced to `ai-features`; unfence to shoot only after #504 merges. Needs live ANTHROPIC key to show ✨ (not Auto-problem) |

## Production checklist

- [ ] **Demo data**: a believable seeded school — Indian student names, a
      teacher, a parent linked to an active child, weeks of activity history so
      dashboards/sparklines/streaks are non-empty. (`seed_demo_data` exists —
      audit it against every shot above.)
- [ ] **Live AI key** in the recording environment so every badge reads
      `✨ AI-generated`, never `Auto-built`.
- [ ] **Recording setup**: clean browser profile, 1920×1080 (+ one 375px mobile
      pass for shot 7/8), cursor highlighting, no bookmarks bar/devtools.
      Tool: OBS or Screen.studio; decide.
- [ ] **Rehearsal doc**: click-by-click path for each shot, verified on the
      current build (the plan routine re-verifies weekly — beats drift).
- [ ] **Voiceover**: record after picture lock; consider a Hindi-subtitled cut
      (on brand for LA).
- [ ] **Launch blockers before publishing the URL** (from ops notes): real
      Anthropic key in prod, DNS apex flip, TLS via cert-manager, GHCR packages
      public.

## Task queue — camera-ready tasks for `openshiksha-execute`

> The plan routine appends dated, concrete tasks here; the execute routine works
> them top-down and checks them off in its PR.

- [x] **T-1 (2026-07-01):** Audit `seed_demo_data` against the shot list.
      **Done ([#503](https://github.com/openshiksha/openshiksha/pull/503)):**
      audit written as a comment block atop the command.
      Findings: every AI dashboard the video films (parent summary, streaks,
      class insights, predictions) reads `edge.Tick` rows — the seed created
      zero ticks and a single student, so those surfaces filmed empty. Fixed in
      the same PR: 5 named Class-10A students (shots 2/3), a 2nd chapter for a
      strong-vs-weak split, ~2 weeks of back-dated Tick history with per-student
      ability profiles, per-student streaks (hero on 14 days), and graded
      submissions. Verified against the analytics fns: class insights now show
      Quadratic=AT_RISK / Linear=PROFICIENT, parent summary + predictions
      non-empty, idempotent across re-runs. **Remaining gap:** derived rows
      (LearningGap/PerformancePrediction/ParentProgressSummary) come from the
      analytics Celery tasks — the recording env must run those once after
      seeding (noted in the command output + docstring).
- [ ] **T-2 (2026-07-01):** Create `docs/launch/assets/` and capture first-pass
      stills of shots 1, 4, 5 via Playwright (reuse the golden-path screenshot
      mechanics) so the script can be judged against real frames.
- [ ] **T-3 (2026-07-01):** Rehearse shot 8 (offline) end-to-end on the dev
      stack and document the exact toggle timing that looks clean on camera.
- [x] **T-4 (2026-07-01):** Audit for a "try it in 60 seconds" CTA path.
      **Done (docs-only, this commit).**

      **Findings:**
      - The plan's assumed path `frontend_modern/src/features/public/` does not
        exist. The landing page is `features/home/HomePage.tsx`, mounted at route
        `/`. Its CTAs are `/login` and `/register/open` — there is **no
        pre-provisioned one-click "demo login" button.**
      - **No shared demo credential is exposed in production.** `seed_demo_data`
        does mint stable demo logins (`student_demo` / `demo1234`, plus
        `teacher_demo`, `parent_demo`, `admin_demo`, `openstudent_demo`, all
        `demo1234`) — and, post-T-1, `student_demo` now lands on a *populated*
        dashboard (streak, history, parent summary). But those accounts only
        exist where the seed has been run (dev), **not** on prod `openshiksha.org`.
      - The only instant self-serve path that works on prod today is
        **`/register/open` → `POST /api/v1/auth/register/open/`**: creates an
        `open_student` with just a username + password (≥8 chars; email/name
        optional), returns a JWT immediately, no email verify / no join code.
        Downside for a launch CTA: a freshly-registered open student lands in an
        **empty** experience (no seeded history), a weaker first impression than
        the `student_demo` dashboard the video itself films.

      **Verdict — this is a launch blocker (do NOT build here):** there is no
      productionised, populated, one-click demo login for a stranger hitting the
      CTA. Two options for the plan routine to decide:
      (a) run `seed_demo_data` in prod and surface read-only `student_demo /
      demo1234` creds on the CTA card (matches what the video shows); or
      (b) point the CTA at `/register/open` and accept/soften the empty first-run.
      Recommendation: (a) for the launch — the seeded hero account is the exact
      experience the film sells.

      **Not yet done:** runtime verification (loading `/` and walking
      `/register/open` on a running dev stack) — the audit above is code-level
      only; the live-walk is left for a shot-list QA pass with the stack up.

- [ ] **T-5 (2026-07-02):** Restore the Marathi (`mr`) UI pilot so shot 7 can
      show three languages as the i18n story promises (content-only, per the
      registry North Star — no consumer edits). Concretely: add
      `frontend_modern/src/shared/i18n/locales/mr.ts` (start from `en.ts`, a
      pilot *subset* is allowed), register it in
      `src/shared/i18n/locales/registry.ts` (widen the `Locale` union to include
      `'mr'`, append a `LOCALES` entry `{ code:'mr', label:'मरा', nativeName:'मराठी',
      htmlLang:'mr', intlLocale:'mr-IN', coverage:'pilot' }`, add an `mr` loader),
      and add its floor to `coverage.test.ts` (line ~23 note "Marathi was removed"
      → re-add). Verify: `npx vitest run src/shared/i18n/` green (registry, parity,
      coverage), and the switcher renders `EN | हिं | मरा`. Backend already accepts
      `mr` (`core/models.py` `preferred_language` choices). This unblocks shot 7's
      three-language claim; leave the video script's language count to the plan
      routine once this lands.
