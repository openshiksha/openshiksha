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
| 1:40–2:05 | Trust & reach | Language switcher EN → हिंदी → मराठी on the student loop; airplane-mode toggle → the assignment keeps working, "Saved offline · will sync"; parent dashboard AI summary | "Three languages. Works without internet. Parents get a plain-language summary. Built for classrooms in India." |
| 2:05–2:30 | CTA | README / architecture diagram / openshiksha.org / GitHub stars button | "OpenShiksha is open source and live. Link below." |

**Open scripting questions:** whether to include the meta-story ("built by
scheduled AI agents") in this video or save it for a separate devlog cut (see
[`ideas.md`](ideas.md) #2); whether PV-3 (generate a whole verified practice
problem) makes the cut once it ships on-screen.

## Shot list

| # | Shot | Route / setup | Demo beat | Status |
|---|---|---|---|---|
| 1 | Describe-to-Build generate + attach | Create Question → Add interactive widget | Beats 2–3 | ⬜ needs rehearsal (use step 0.25 axis; ¾ snap quirk) |
| 2 | 🎲 randomized-per-student toggle | Same prompt box, checkbox on | Beat 5 | ⬜ needs two demo student logins |
| 3 | Two students, different numbers | Open question as 2 students, split screen | Beat 4/5 | ⬜ needs seeded students with real names |
| 4 | Student drags point → graded | Assignment detail as student | Beat 3 | ⬜ |
| 5 | Step-solver live ✓/✗ + coach auto-feed | `/widgets/dev?kind=step-solver` (or QuestionCard if landed) | Beats 7, 10 | ⬜ decide playground vs. real student view |
| 6 | ✨ AI explanation of wrong step | Same, "Why is this wrong?" | Beat 9 | ⬜ requires live ANTHROPIC key (must show ✨, not Auto-) |
| 7 | Language switch en→hi→mr | Student dashboard, switcher | LA initiative | ⬜ |
| 8 | Offline: airplane mode mid-assignment | DevTools offline toggle, banner + queued save | MSO initiative | ⬜ rehearse replay-on-reconnect |
| 9 | Parent AI weekly summary | Parent dashboard | ASA initiative | ⬜ needs child with real activity history |
| 10 | B-roll: README, Mermaid diagram, PR history | GitHub | — | ⬜ |

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

- [ ] **T-1 (2026-07-01):** Audit `seed_demo_data` against the shot list —
      does it produce a school with named students, a parent-child link, and
      enough submission history for sparklines/streaks/parent-summary? Write
      findings + gaps as a comment block at the top of the command file or a
      note here; fix small gaps in the same PR.
- [ ] **T-2 (2026-07-01):** Create `docs/launch/assets/` and capture first-pass
      stills of shots 1, 4, 5 via Playwright (reuse the golden-path screenshot
      mechanics) so the script can be judged against real frames.
- [ ] **T-3 (2026-07-01):** Rehearse shot 8 (offline) end-to-end on the dev
      stack and document the exact toggle timing that looks clean on camera.
