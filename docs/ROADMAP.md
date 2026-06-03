# OpenShiksha Roadmap

> **Single source of truth** for what's shipped and what's left.
> The per-day `docs/daily-plans/*.md` files are point-in-time snapshots; this
> file is the living tracker. Update it whenever a PR merges.

**Last updated:** 2026-05-30 (after class misconception insights branch)

---

## 🔜 Remaining (what's left)

In priority order. Nothing below is started unless noted.

| # | Task | Type | Notes |
|---|------|------|-------|
| 1 | **P8 — operational bulk Cabinet import run** | Ops | The importer (`import_cabinet_questions`) shipped in PR #100. This is the *operational* run: clone `openshiksha-cabinet`, run the importer with a mapping file against real content. |
| 2 | **Phase 2 — UI rebuild** | Frontend | Design-system pass to Linear/Vercel-quality polish; bottom tab bar on mobile. Large, follows the feature build-out. |
| 3 | **Teacher AI Assistant (broader)** | AI | Weekly class reports (#95), class misconception insights, auto-assignment drafts, and open-ended/free-text grading (this PR) shipped. Remaining: teacher-facing dashboard cards surfacing these (cluster API, open-grade review queue). Future. |
| 4 | **i18n toggle (`en` / `hi`) on parent insights** | Frontend | The parent-summary API already accepts `language`; expose a header toggle once a global language switcher lands. |

---

## ✅ Completed

Grouped by area. PR numbers in parentheses; P-codes are the cycle's priority labels.

### AI features
- Smart Analytics & Insights — learning gaps, class insights, perf prediction (#55)
- Content Recommendations & Daily Practice Plans (#60)
- Adaptive Learning Engine — mastery, spaced repetition, learning paths (#62)
- AI analytics pipeline activated end-to-end (#71)
- Natural Language Explanations — Gemma 4 / Claude cascade (#92)
- **P0** — LLM question generation + edit mode + add-to-problem-set (#94)
- Teacher AI Assistant — Weekly Class Summary Reports (#95)
- Intelligent Hint System — progressive hints + misconception detection (#102)
- **Parent Intelligence Dashboard — backend** (model, analytics, LLM cascade, viewset, Celery task) (#107)
- **Parent Intelligence Dashboard — frontend** (`/parent/insights` narrative + alerts + home activities) (#109)
- Weekly parent-summary email + Monday Celery beat (`enqueue_weekly_parent_summaries` + `notify_parent_weekly_summary`) (commit a8faf034)
- **Class Misconception Insights** — class-level aggregation of `StudentMisconception` rows into ranked clusters for teachers
- **AI Assignment Draft Builder** — auto-assembled draft assignments targeting class weaknesses (#119 area)
- **AI-Assisted Open-Ended Response Grading** — `SHORT_ANSWER` type + rubric + LLM-suggested score/feedback with teacher review (this PR)

### Platform foundation
- Question Bank + Assignment Pipeline models and REST API (#54)
- Analytics engine + grading pipeline (#56)
- Assignment detail page, seed command, teacher UI (#64)
- Teacher analytics, student proficiency page, question authoring UI (#66)
- Teacher assignment detail, problem-set builder, Croupier phase 1 (#68)
- Croupier phase 2 — variable substitution for numeric questions (#73)

### Student experience
- Student learning-path page (#76)
- Proficiency trend snapshots (#80)
- Mobile-first responsive pass — navbar hamburger + student pages (#82)
- SRS practice drill mode — closes the spaced-repetition loop (#83)
- Activity streaks, content search, remedial auto-creation (#84)
- Drill sessions wired into proficiency engine + streak (#85)
- **P2** — `image_url` support on `QuestionSubpart` (#86)
- **P3** — per-student remedial assignments via `target_student` FK (#87)
- Streak grace-day mechanic + milestone tier badges (#89)

### Teacher tools
- Teacher question-mistake analytics (#75)
- Variable-constraints authoring UI in CreateQuestionPage (#77)
- Teacher question bank, SRS due panel, parent dashboard (#79)
- Teacher announcements — broadcasts to a subject room (#99)

### Parent experience
- Parent assignment view (#81)
- (Parent Intelligence Dashboard — see AI features, #107 / #109)

### School admin
- **P4 backend** — School Admin API foundation (`IsSchoolAdmin`, classroom CRUD, enrollment, roster) (#103)
- **P4 frontend** — School Admin UI (#105)

### Content modules
- **P7** — Concierge public enquiry form for prospective schools (#97)
- **P6** — Lodge chapter-linked instructional videos (#98)
- **P8** — Cabinet question import + worked solutions (importer, solution/hint fields, student reveal) (#100)

### Onboarding
- Self-registration, classroom join codes, open-student browse, profile settings (#91)

### Email / notifications
- Phase 1 email notifications — grading complete + remedial assigned (#90)
- **P5** — email assignment due-date reminders (Celery beat, daily 06:00) (#106)

### Infra / CI / security
- Linting, dependency audit, pre-commit hooks; black/isort enforcement; frontend lint/type-check/test job; mypy + npm audit; SQLite test settings; coverage threshold raised to 90% and sticky PR coverage comment; missing-migration detection; Dependabot; migration dedup; Django/Pillow/pytest CVE upgrades
  (#57, #58, #61, #63, #67, #69, #70, #72, #74, #78, #88, #93, #96, #101, #108)
