# Initiative — V2 "Chalk & Unlock" design overhaul

> Replace OpenShiksha's generic blue-template UI with a warm, branded,
> **professional-but-fun** design system — built page by page across many
> sessions, with the system itself getting better each session.
>
> Read [`README.md`](README.md) for the per-session loop. This doc is the single
> source of truth for the design language, the backlog, and progress.

---

## North Star

OpenShiksha is used by **children and their parents** in Indian K-12. The product
must feel **trustworthy and professional** (a parent is judging whether to rely on
it for their child's education) while being **warm and a little fun** (a 12-year-old
should *want* to open it). Every detail is intentional — nothing generic, nothing
childish, nothing sterile.

The visual identity already exists in the legacy brand: an **orange graduation cap
whose negative space forms a keyhole** — *education unlocks potential*. V2 builds
the entire system around that idea: **"Unlock."** Progress unlocks. Mastery
unlocks. The keyhole and a warm "chalk-on-paper" palette give the product a
distinctive, human, classroom-rooted feel that no competitor template has.

**Done looks like:** every authenticated surface and the marketing/auth surfaces
share one coherent, branded, accessible, responsive language; a parent finds it
credible at a glance; a child finds it inviting; and a new contributor can build a
new screen in-language in minutes using `src/shared/ui` + the tokens.

---

## Principles — "Chalk & Unlock"

1. **Warm, not cold.** Surfaces are warm paper (`ink`-tinted off-white), not the
   default cold gray/blue. Text is warm `ink`, not `#000`. This single choice is
   what separates us from every blue SaaS template.
2. **Orange with restraint.** The brand orange (`#FF6F00`) is the *action /
   progress / unlock* colour. It earns attention because it's not everywhere.
3. **Editorial typography.** A characterful display serif (**Fraunces**) for
   headings + clean **Inter** for UI/body. The serif is where "intentional and a
   little human" comes from; the sans keeps it credible and legible.
4. **The keyhole is the motif.** Use it deliberately — the logo, progress/mastery
   ("unlocked"), empty states, loading. Never decorative noise.
5. **Calm density.** Generous spacing and clear hierarchy. Kids and stressed
   parents both need an interface that doesn't shout (except where it should:
   one clear primary action per screen).
6. **Fun is in the details, not the layout.** A chalk-underline on the active
   nav, a gentle float on the brand mark, a satisfying "unlock" on achievement —
   micro-delight inside a professional frame. No confetti-by-default.
7. **Accessible by default.** AA contrast, focus-visible rings, reduced-motion
   honoured, semantic HTML. Non-negotiable for a product used by children.

---

## Foundation / Scaffold (what exists now — build on this, don't reinvent)

Established in the kickoff session (2026-05-30):

- **Brand assets** — `frontend_modern/public/brand/logo-orange.png`,
  `logo-inverted.png`, and `public/favicon.ico` (migrated from the legacy app);
  `index.html` wired to the real favicon + `theme-color #FF6F00` + the Fraunces
  and Inter font links.
- **Design tokens** — `frontend_modern/tailwind.config.js`:
  - `brand` 50–900 (anchor **`brand-600 = #FF6F00`**, the legacy logo orange).
  - `ink` 50–900 (warm chalkboard neutrals for text/surfaces).
  - ~~`primary` 50–900 (legacy blue)~~ — removed in M6-02 (2026-06-04, #193)
    once every authenticated surface moved to `brand`.
  - `boxShadow`: `soft`, `card`, `lift` (warm-toned elevation).
  - `fontFamily`: `sans` (Inter), `display` (Fraunces).
  - `animation`: `fade-up`, `fade-in`, `float`.
- **Brand CSS layer** — `frontend_modern/src/index.css`: warm `body` base,
  Fraunces headings, and seed component classes (`.btn-brand`, `.btn-ghost`,
  `.os-card`, `.input-brand`, `.chalk-underline`, `.bg-paper`, `.bg-chalkboard`).
- **Seed component library** — `frontend_modern/src/shared/ui/`: `Logo`,
  `Button`, `Card`, `Badge`, `Skeleton`, `RichContent` + `renderRichContent`,
  `InteractiveWidget`, `Input`/`Textarea`/`Select`, `Stat`, `SectionHeading`,
  `EmptyState`, `LoadingSpinner`, `ErrorBoundary` — barrel `index.ts` + conventions
  `README.md` every session must follow.
- **Living showcase** — route `/design` (`features/design/DesignSystemPage.tsx`)
  renders the tokens + every `ui/` component. **Every new primitive must be added
  here** — this is how we keep the system visible and prevent drift.

---

## Design language reference

### Colour tokens

| Token | Hex | Use |
|---|---|---|
| `brand-600` | `#FF6F00` | Primary actions, active state, progress fill, the mark. The "unlock" colour. |
| `brand-500/700` | `#FB7705` / `#CC5800` | Hover / pressed. |
| `brand-50/100` | `#FFF8F1` / `#FFEEDC` | Tinted backgrounds, soft highlights, app paper. |
| `ink-900/800` | `#0F0E0D` / `#1A1816` | Headings, chalkboard surfaces. |
| `ink-600/500` | `#34302B` / `#4A463F` | Body text. |
| `ink-400/300` | `#736D63` / `#A29C93` | Muted text, captions. |
| `ink-100` | `#E7E5E2` | Hairline borders on paper. |
| Semantic | Tailwind `emerald` / `amber` / `rose` | success / attention / urgent — keep alert semantics consistent with the parent-insights `AlertsPanel`. |

> **Rule:** components reference **tokens only** — never a raw hex. If a needed
> shade is missing, add it to the token scale (and note it in the ledger), don't
> inline it.

### Typography

- **Display (`font-display`, Fraunces):** page titles, section headers, big
  numbers, empty-state headlines. Weights 500–700; let it have optical size.
- **Body/UI (`font-sans`, Inter):** everything else. Weights 400–600.
- Scale (suggested): display `text-3xl/4xl`, section `text-xl/2xl`, body
  `text-base`, caption `text-sm`. Generous `leading`.

### The keyhole motif

- **Logo** — `<Logo />` from `ui/`. Mark on dark = `logo-orange.png`; full
  lockup adds the Fraunces wordmark. A subtle `animate-float` is allowed on hero
  marks only.
- **Progress = unlocking** — mastery rings/bars fill in `brand`; a reached
  milestone reads as "unlocked" (keyhole icon + brand, not a generic check).
- **Empty / loading** — prefer a keyhole-derived motif over a generic spinner
  where it fits the surface.

### Surfaces & elevation

- App background: warm paper (`bg-paper` / `brand-50`), never `bg-gray-50`.
- Cards: `.os-card` (white, warm `ink-100` hairline, `shadow-card`, `rounded-xl2`).
- Chalkboard panels (auth hero, section dividers): `.bg-chalkboard` (`ink-900`)
  with chalk-toned text — the legacy blackboard heritage, used sparingly.

### Motion

- One orchestrated entrance per view (`animate-fade-up` with staggered
  `animation-delay`), not scattered micro-animations.
- Hover/press states on all interactives. Always gate non-essential motion behind
  `@media (prefers-reduced-motion: reduce)`.

---

## Backlog (prioritised, session-sized increments)

Each increment ≈ one PR. **Pull the top unblocked item.** `[x]` = shipped (see
Ledger). Split any item that won't fit one session.

### M1 — Foundation  *(✅ complete)*
- [x] `M1-01` Brand assets + favicon + fonts wired into `index.html`.
- [x] `M1-02` Token system in `tailwind.config.js` (brand, ink, shadows, motion).
- [x] `M1-03` Brand CSS layer in `index.css` (base + seed component classes).
- [x] `M1-04` Seed `ui/` library (Logo, Button, Card, Badge) + conventions README.
- [x] `M1-05` `/design` living showcase route.
- [x] `M1-06` `Input`/`Textarea`/`Select`, `Stat`, `SectionHeading`, `EmptyState`
  primitives shipped 2026-06-02; `Skeleton` shipped 2026-05-30; `Badge` severity
  tones live since kickoff. All exported from `ui/index.ts` + rendered on `/design`.

### M2 — Global shell  *(every page inherits this — do first)*
- [x] `M2-01` Reskin **App Shell** (`AppShell` + `Navbar`): real `<Logo/>`, warm
  paper background, brand active-nav (chalk underline), warm user menu.
- [x] `M2-02` Mobile nav polish — shipped 2026-06-04 (#198). Hamburger sheet
  repurposed as an Account drawer (now that M5-01 bottom tabs carry primary
  nav); tokens swept; `aria-current` / `aria-haspopup` / dynamic
  hamburger-label / focus-visible rings / ESC closes both dropdowns; safe-area
  inset top.
- [x] `M2-03` Global states: branded `LoadingSpinner`, `NotFoundPage` (404 route),
  `ErrorBoundary` shipped 2026-06-02. Toast theming deferred (no toast lib
  currently wired — add when first needed).

### M3 — Auth & marketing  *(first impression; self-contained, low-risk)*
- [x] `M3-01` **Login** → chalkboard-left / paper-right brand layout (flagship).
- [x] `M3-02` Register + Register-school + Register-open migrated to the V2
  chalkboard/paper layout 2026-06-02, using new `ui/Input`.
- [x] `M3-03` Public **Enquire** page — shipped 2026-06-04 (#199 + #200 follow-up
  for a duplicate "Back to sign in" link). Composed via the shared `AuthLayout`
  (chalkboard hero + paper form); uses `ui/Input`/`Textarea`/`Button`; success
  state via `EmptyState` keyhole motif.
- [x] `M3-04` **Home page** at `/` — legacy-inspired (chalkboard hero →
  Practice/Evaluate/Analyse → mission + teacher photo → "Start now" → features),
  new branding, legacy hero images, branded Login CTA. Logo links home everywhere.

### M7 — Functional parity & enrichment  *(HIGH PRIORITY — the frontend must do everything the legacy did, better)*

> Surfaced by reviewing the running app as `student_demo` (see
> `screenshots/questions-broken-before.png`). These are functional, not purely
> visual — but they are what "fully featured" means and gate real classroom use.
> If this milestone grows, graduate it to its own initiative.

- [x] `M7-01` **Question content rendering — LaTeX + HTML.** Shipped 2026-05-30.
  New `shared/ui/RichContent` primitive: DOMPurify-sanitised HTML + KaTeX over
  `$…$` / `\(…\)` (inline) and `$$…$$` / `\[…\]` (block). Wired into
  `QuestionCard` (question text, MCQ options, hints, worked solutions), the SRS
  drill (via `QuestionCard`), and the teacher `CreateQuestionPage` live
  preview. Showcased on `/design`.
- [x] `M7-02` **Question variable substitution ("widgets").** Backend engine
  (`croupier.py`: `sample_variable_values`, `substitute_variables`,
  `substitute_variables_for_student`) was already complete and wired into
  `QuestionSubpartStudentSerializer` — but `QuestionViewSet.get_serializer_class`
  returned the teacher-safe `QuestionSerializer` for *every* role, so students
  hitting `/student/browse/practice/<chapter>` saw raw `{{k}} {{j}} {{l}}` tokens.
  Fixed 2026-06-02 (#140) by role-switching the viewset to return
  `QuestionWithSubpartsStudentSerializer` for STUDENT/OPEN_STUDENT on list+retrieve.
  Tokens now substitute deterministically per `(student_id, subpart_id)`; 4 new
  regression tests; 777 backend tests passing.
- [~] `M7-03` **List-page filtering / search / sort actually works.** Browse
  Grade filter (#194) + Question Bank search-dedup + Grade filter parity (#197)
  shipped 2026-06-04. **Remaining:** Question Bank chapter-filter *UI* (backend
  already supports `?chapter=`); assignment-list filters (student/teacher
  views currently group by status only — no UI controls). Both small frontend
  follow-ups.
- [x] `M7-04` **Feature-parity audit vs. legacy** — shipped 2026-06-04 in
  [`legacy-feature-parity.md`](legacy-feature-parity.md). At-a-glance table
  per legacy app, by-audience capability tables, known TODO list (7 items),
  and a deletion checklist for retiring a legacy app.
- [x] `M7-05` **`seed_demo_data` idempotency.** Fixed 2026-06-02 (#141) — the
  command was crashing with `MultipleObjectsReturned` on any DB with cabinet
  imports because `Question.get_or_create(school, standard, subject, chapter,
  type, difficulty)` matched multiple imported rows. Now uses a `seed-demo`
  `QuestionTag` as an idempotency namespace: stale `seed-demo`-tagged questions
  are deleted and recreated fresh each run, never touching cabinet/teacher
  content. **Bonus**: command now creates all 5 demo accounts (`parent_demo`,
  `admin_demo`, `openstudent_demo` in addition to the original student/teacher)
  and links `parent_demo → student_demo` so every role works on a fresh stack.

### M4 — Product surfaces  *(✅ complete 2026-06-04 — every authenticated surface on V2)*
- [x] `M4-01` **Student Dashboard** migrated to V2 brand 2026-06-02.
- [x] `M4-02` Parent Dashboard + Parent Insights — shipped 2026-06-03 (#181).
- [x] `M4-03` **Teacher Dashboard** migrated to V2 brand 2026-06-02.
- [x] `M4-04` Admin Dashboard + Classroom manage — shipped 2026-06-03 (#182).
- [x] `M4-05` Assignment detail (student) + SRS drill + `QuestionCard` /
  `AssignmentCard` / `AssignmentList` — shipped 2026-06-03 (#185 / a62f7464).
- [x] `M4-06a` Proficiency cluster + `DueForReviewPanel` / `RecommendationsPanel` /
  `StreakBadge` — shipped 2026-06-03 (#183).
- [x] `M4-06b-i` Browse + Browse-Practice — shipped 2026-06-04 (#188).
- [x] `M4-06b-ii` Learning Path + `VideosPanel` — shipped 2026-06-04 (#189).
- [x] `M4-07a` Teacher dashboard panels (`ClassHealthPanel` / `WeeklyReportPanel` /
  `ClassroomCodeWidget`) — shipped 2026-06-04 (#190).
- [x] `M4-07b` `TeacherAssignmentDetailPage` — shipped 2026-06-04 (#191).
- [x] `M4-07c` Create-Question authoring page — shipped 2026-06-04 (#192). Create
  problem-set / Create assignment / Question bank were already V2-native by #185.
- [x] `M4-08` Profile / settings (`shared/ProfilePage.tsx`) — shipped 2026-06-03 (#180).

### M5 — Mobile & responsive pass
- [x] `M5-01` Bottom tab bar for primary roles on mobile — shipped 2026-06-04 (#195).
  Role-aware (Student/Open: Home/Browse/Path/Profile · Teacher: Home/Questions/Profile ·
  Parent: Home/Profile · Admin: School/Profile). Above `env(safe-area-inset-bottom)`;
  hidden on `sm:` and above.
- [x] `M5-02` Per-surface responsive audit — shipped 2026-06-04 (#201). Two
  table-overflow fixes (BrowsePage chapter table, ClassHealthPanel table);
  rest of the migrated surfaces audited clean. **Follow-up:** 44×44 touch
  targets on student practice (flagged in #195 change doc); PWA install /
  offline question viewing.

### M6 — Hardening
- [x] `M6-01` Accessibility audit (AA, focused baseline) — shipped 2026-06-04
  (#202). Skip-to-main link + `id="main-content"` landmark; full dialog
  semantics on the QuestionBank add-to-set sheet (role=dialog, aria-modal,
  aria-labelledby, ESC, initial focus on close); image alt parity on
  QuestionPreviewPanel. **Follow-up:** keyboard walkthrough, screen-reader
  spot-check (VoiceOver/NVDA), CreateQuestionPage tab-order audit, axe-core
  CI gating — promote to its own initiative if scope grows.
- [x] `M6-02` Retire the legacy `primary` (blue) token — shipped 2026-06-04 (#193).
  Palette + the four legacy helper classes (`.btn-primary`, `.btn-secondary`,
  `.card`, `.input`) deleted; 0 src/ consumers verified before merge.
- [~] `M6-03` Visual-regression screenshots — spec shipped 2026-06-04 (#203).
  Playwright `visual.spec.ts` covers `/design`, `/`, `/login`, `/enquire` at
  desktop + mobile; describe block is `.skip`-d until Linux baseline PNGs are
  generated on CI (Windows-generated PNGs would never match the CI runner).
  Activation = one CI run with `--update-snapshots` + commit + remove the
  `.skip`. Authenticated-surface snapshots need a separate `playwright`
  project against Docker; deliberate follow-up.

> M4 is closed. The next active milestones are **M2-02** (mobile nav polish),
> **M3-03** (Enquire), **M5-02** (responsive audit), **M6-01** (a11y audit),
> **M6-03** (visual-regression set), and the remaining slice of **M7-03**
> (Question Bank + assignment-list filter parity). Pull whichever is the
> highest-value unblocked item.

---

## Definition of Done (every increment)

An increment is done only when **all** hold:

- [ ] Uses **tokens + `ui/` components only** — no raw hex, no `primary`/`indigo`/
  `blue`/cold-gray classes in touched code.
- [ ] **Responsive** (≥320px) and **keyboard-accessible** (focus-visible, labels,
  roles); AA contrast; honours `prefers-reduced-motion`.
- [ ] Any new primitive is **added to `/design`** and exported from `ui/index.ts`.
- [ ] `npm run type-check`, `npm run lint`, `npm run build`, and `npm test` pass.
- [ ] **Verified in the real Docker stack**, not just isolated Vite: bring up
  `docker compose up -d --build postgres backend frontend`, `migrate` +
  `seed_demo_data`, log in as `student_demo` / `demo1234`, and **screenshot the
  result** into `docs/initiatives/screenshots/`. Embed the screenshots in the PR
  so they can be validated. (Hide the React-Query devtools panel before
  shooting; on Windows, `docker compose restart frontend` if the bind-mount
  didn't hot-reload.)
- [ ] The **Progress Ledger** below is updated and a `docs/changes/<date>-*.md`
  written, linking this initiative.
- [ ] No existing functionality regressed (routes, role guards, data flows intact).

---

## Continuous Improvement (step 3 — do one each session)

Leave the system better than you found it. Pick one:

- Replace a one-off inline style somewhere with a `ui/` component or token.
- Add a missing token shade / semantic alias instead of an inline value found
  during the increment.
- Improve a `ui/` component's API, a11y, or docs; add a usage example to `/design`.
- Delete dead CSS / duplicated patterns; consolidate two near-identical components.
- Tighten a convention in `ui/README.md` based on something that bit you.
- Add/refresh a screenshot in the regression set.

Record the improvement in the ledger's "Hardening" column so the gains are visible.

---

## Progress Ledger (append-only)

| Date | Increment | PR | Hardening done | Learning / note |
|---|---|---|---|---|
| 2026-05-30 | M1-01…05 foundation scaffold | _(this branch)_ | Established token-only rule; retained `primary` for un-migrated pages | Legacy logo orange sampled to `#FF6F00`; pairing Fraunces+Inter gives the "professional but warm" read. Shell (`M2-01`) is the right next step — it's global. |
| 2026-05-30 | M2-01 shell, M3-01 login, M3-04 home page | _(this branch)_ | Verified in real Docker stack; logo links home everywhere | Reviewing as `student_demo` exposed `M7` (question HTML/LaTeX/variables render raw — see `screenshots/questions-broken-before.png`). Windows Docker bind-mount doesn't always hot-reload Vite — `restart frontend` to pick up late edits. Backlog grew an `M7` functional-parity milestone; this is now the highest-value work after the shell. |
| 2026-05-30 | M7-01 question HTML+LaTeX rendering, M1-06 partial (`Skeleton`) | `feat/2026-05-30-question-rich-content` | Extracted shared `RichContent` primitive; deleted duplicate `renderMixedContent` from `QuestionCard` + `CreateQuestionPage`; added `prose-osh` brand prose styles; `Skeleton` primitive shipped and swapped into the SRS drill loading state. | Splitting the renderer into `renderRichContent.ts` (pure) and `RichContent.tsx` (component) kept fast-refresh's "component-only exports" rule happy. KaTeX warns about "quirks mode" inside happy-dom test env (harmless — the template-element-walk path doesn't ship a doctype); production browsers are fine. `M7-02` (variable substitution) is the next pull. |
| 2026-06-02 | M1-06 finish primitives (`Input`/`Textarea`/`Select`, `Stat`, `SectionHeading`, `EmptyState`) | #135 | Every M1-06 primitive added to `ui/index.ts` and rendered on `/design`. | Wrote the input chrome as a base `.input-brand` CSS class so `Input`/`Textarea`/`Select` share one focus-ring/error-state implementation. All M4 page migrations now compose these instead of hand-rolling form fields. |
| 2026-06-02 | M2-03 global states — `LoadingSpinner` (keyhole motif), `NotFoundPage`, `ErrorBoundary` | #136 | Branded full-screen fallbacks; reduced-motion honoured on spinner. | No toast lib currently wired into the app — deferred toast theming until first real use rather than adding a dependency speculatively. |
| 2026-06-02 | M3-02 register flow → V2 (Register, Register-school, Register-open) | #137 | All three pages share the Login chalkboard/paper layout; using new `ui/Input`. | Reusing the Login layout keeps "first impression" coherent — every unauthenticated surface now reads as the same product. |
| 2026-06-02 | M4-01 Student Dashboard → V2 | #138 | All `indigo`/`gray-50` removed from the dashboard's own JSX + empty/enrolment state; uses `Stat`, `SectionHeading`, `EmptyState`, `.os-card`. | Child panels (`DueForReviewPanel`, `RecommendationsPanel`, `AssignmentCard`, `StreakBadge`) intentionally left for M4-06 so this PR stays atomic. |
| 2026-06-02 | M4-03 Teacher Dashboard → V2 | #139 | Same treatment for Teacher Dashboard + container chrome of its panels. | `InterventionsPanel` (merged same day) was already token-clean, so only its host needed restyling. |
| 2026-06-02 | M7-02 variable substitution endpoint fix | #140 | 4 new regression tests; `BrowsePracticePage` stale `LoadingSpinner` import fixed in the same PR; `scripts/init_db.sql` added (Docker auto-creates it as a dir when missing, crashing postgres init). | The substitution engine was *already complete* — the bug was a single missing role-switch in `QuestionViewSet.get_serializer_class`. The SRS drill and assignment detail used the correct serializer; only the browse endpoint was wrong. Cheap fix, huge user-facing impact (no more raw `{{k}}` tokens for students). |
| 2026-06-02 | M7-05 seed_demo_data idempotency | #141 | `seed-demo` `QuestionTag` namespace; all 5 demo accounts now created by the command + `parent_demo → student_demo` linkage. | Tag-namespaced delete/recreate is cleaner than tightening `get_or_create` keys — works regardless of what other questions share the same (chapter, type, difficulty) combo, and is fully scoped (can never touch cabinet content). Same pattern fits future "demo content reset" needs. |
| 2026-06-04 | M4-06b-i Browse cluster → V2 | #188 | `BrowsePage` + `BrowsePracticePage` compose `SectionHeading`/`Select`/`os-card`/`Button`/`Badge`/`EmptyState`; table moved to warm `ink-*` with `brand-50/40` hover. | `QuestionCard` was already V2 from #185 so the practice page only needed chrome work — kept the scope tight by explicitly leaving filter wiring for M7-03. |
| 2026-06-04 | M4-06b-ii Learning Path + Videos → V2 | #189 | Path steps adopt the brand "unlock" motif (emerald check / brand-orange unlocked keyhole / muted locked keyhole + vertical `ink-100` rail); aria `progressbar` on the path-progress bar; `VideosPanel` → `os-card`. | Shape-distinct status icons (keyhole/check/lock) keep the path readable in colourblind modes — not relying on colour alone is a Definition-of-Done win. |
| 2026-06-04 | M4-07a Teacher dashboard panels → V2 | #190 | `ClassHealthPanel` / `WeeklyReportPanel` / `ClassroomCodeWidget` adopt severity tones (rose/amber/emerald) matching `AlertsPanel`; weekly summary card → `brand-50/60`; join code chip → `brand-50` + `ring-brand-100`. Disclosure toggles gained `focus-visible` rings; chevron honours `motion-reduce`. | The Teacher Dashboard host (#139) already V2 — these were the only three child panels still wearing blue, so reskinning them lets the whole page read as one surface. |
| 2026-06-04 | M4-07b Teacher assignment detail → V2 | #191 | KPIs → 3 `Stat` blocks (Due Stat surfaces an Overdue delta pill); submission table picks up the Admin-table treatment from #182 (`bg-ink-50` `font-display` header, `brand-50/40` hover rows); Hardest Questions → `os-card` shell with `rose-500` bars. Submission progress bar gained `role="progressbar"` + aria-value attrs. | Reusing the Admin classroom-manage table style across two different roster surfaces is the kind of compounding the initiative is designed for — both pages now share one "roster table" treatment, so the next list/table page is a near-zero design decision. |
| 2026-06-04 | M4-07c CreateQuestionPage → V2 (**closes M4**) | #192 | ~90 legacy refs swept in one PR via a deterministic class-name mapping (`indigo→brand`, `gray→ink`, `red/green→rose/emerald`); page heading uplifted to `font-display`; all form controls now `focus:ring-brand-500`. AI panel and active subpart tab now wear brand orange. | The plan budgeted a possible "split out the variable-constraints panel into M4-07c-2" fallback — wasn't needed. Class-name-only sweeps of dense legacy files are reviewable in one PR when you resist refactoring state in the same change. RichContent + AI state machine preserved byte-for-byte. |
| 2026-06-04 | M6-02 retire `primary` blue token | #193 | Deleted `primary-*` palette + `.btn-primary` / `.btn-secondary` / `.card` / `.input` legacy helper classes; refreshed the V2-brand and top-of-file comments. 0 `src/` consumers of the removed tokens/classes verified beforehand. | M4 closing immediately unlocked M6-02 — once the last surface lands on V2 there's nothing left holding the legacy palette in place. Worth doing as its own atomic cleanup PR so the deletion is reviewable. |
| 2026-06-04 | M7-03 browse Grade filter fix | #194 | Backend `browse_chapters` matches `standard__number` (the dropdown sends standard *numbers* 1..12, not PKs); 4 regression tests covering standard, subject, combined, unfiltered; 163 api tests pass. | The endpoint had always been wrong — only worked by coincidence on dev DBs where Standard PK happened to equal `number`. Surfaced because M4-06b-i made the Browse filter UI visible/branded. Question Bank + assignment-list filter parity still on the M7-03 backlog. |
| 2026-06-04 | M5-01 mobile bottom tab bar | #195 | New `BottomNav.tsx` (~170 LOC, role-aware, inline SVG icons, `aria-current` + `aria-label="Primary"`, focus-visible brand ring); above `env(safe-area-inset-bottom)`; hidden `sm:` and up. 5 vitest tests cover role tab sets + prefix-match active highlight. `AppShell` now adds `pb-24 sm:pb-8` so content clears the bar. | Hamburger menu intentionally kept for secondary actions (Profile, Sign out, deep-links like Proficiency) — the bottom bar is for *primary* navigation, not a total replacement. That separation keeps the surface area small and the tabs uncluttered. |
| 2026-06-04 | M7-03 Question list dedupe + Grade filter parity | #197 | `QuestionViewSet.get_queryset` ends with `.distinct()` (search across `subparts__question_text` + `tags__name` no longer multiplies rows); standard filter matches `standard__number` to mirror Browse (#194). 4 new regression tests; 167 api tests pass. | Surfaced once the Question Bank UI exercised search seriously — the same kind of join-multiplies-rows bug Django emits whenever a `search_fields` walks an M2M/reverse-FK. `.distinct()` at the queryset tail is the cheapest reliable fix; the regression tests lock it in. |
| 2026-06-04 | M2-02 mobile nav polish + a11y | #198 | Hamburger sheet repurposed as an Account drawer (identity row, Profile, student-only My Progress, Sign out — no longer duplicating the bottom-tab primary nav). Tokens swept (`gray-*`→`ink-*`, `red-*`→`rose-*`). `aria-label="Top"` on `<nav>`; `aria-current="page"` on active desktop links; `aria-haspopup="menu"` + `role="menu"`/`menuitem` on the avatar dropdown; dynamic hamburger `aria-label`; ESC closes both dropdowns + returns focus to the toggle; focus-visible brand rings throughout; `pt-[env(safe-area-inset-top)]`. | A11y plumbing added at the `Navbar` level (one ESC handler, one focus-visible utility) so the rest of the app inherits the behaviour without per-component wiring. Mobile sheet shrinking to "account only" was the right move *because* M5-01 had just shipped — the bottom bar carries the primary nav. |
| 2026-06-04 | M3-03 Public Enquire page → V2 | #199 + #200 | `EnquirePage` wraps in shared `AuthLayout`; form rebuilt on `ui/Input`/`Textarea`/`Button`; success state uses `EmptyState` keyhole motif; rose-* error banner. Follow-up #200 removed a duplicate "Back to sign in" link from the success state's footer. | Last external-facing surface still on the legacy indigo gradient — wrapping it in `AuthLayout` proved the pattern composes for any new public page in minutes. The duplicate-link follow-up was a 5-min visual bug surfaced by the user immediately after merge; treated as its own atomic PR. |
| 2026-06-04 | M5-02 per-surface responsive audit | #201 | BrowsePage chapter table → `overflow-x-auto` + `min-w-[24rem]` floor so long chapter names don't squash the Practice button. ClassHealthPanel table wrapped in `-mx-1 overflow-x-auto` + `min-w-[22rem]` to absorb long chapter names and wide X/Y counts. Rest of M4 surfaces audited clean. | The dashboards/Profile/Proficiency surfaces inherited their responsive rhythm from `Stat`/`SectionHeading`/`grid-cols-1 sm:grid-cols-N` — *because* they're composed from primitives, the audit found nothing to fix in them. Tables (raw `<table>` markup, not a primitive yet) were the only weak point — argues for a `Table` primitive sometime. |
| 2026-06-04 | M6-01 accessibility audit (focused baseline) | #202 | Skip-to-main link in `AppShell` (sr-only-until-focused brand pill) + `id="main-content" tabIndex={-1}` landmark. `QuestionBankPage` add-to-set side-sheet promoted to a proper dialog: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, descriptive close `aria-label`, ESC handler, initial focus on close button, focus-visible brand ring. `QuestionPreviewPanel` image alt switched from `""` to `"Question diagram"` for parity with `QuestionCard`. | Skip link / main-landmark is *the* foundational a11y move — every page in the app inherits it via `AppShell`. Dialog semantics on the add-to-set sheet matter because it's the only modal surface in the V2 stack; making it correct sets the pattern for any future dialog. Full keyboard walkthrough + screen-reader spot-check + axe-core CI are explicit non-goals; flagged for a dedicated a11y initiative. |
| 2026-06-04 | M6-03 visual-regression spec scaffold | #203 | New `e2e/visual.spec.ts` covers `/design` + `/` + `/login` + `/enquire` at desktop (1280×800) + mobile (375×720), 8 snapshots total. `maxDiffPixelRatio: 0.02`; waits on `document.fonts.ready` so Fraunces/Inter character widths settle pre-snapshot. `test:e2e:update-snapshots` npm script. **`test.describe.skip` until Linux baselines are seeded on CI** (Windows PNGs would never match the Linux runner). | The honest answer to "where do we keep visual baselines on Windows-dev / Linux-CI without false diffs" is: on CI. Skipping the spec until that happens keeps CI green; the activation steps live in the change doc. Authenticated-surface snapshots require a separate Playwright project against Docker — deliberate follow-up. |
| 2026-06-04 | M7-04 legacy feature-parity audit | this PR | New `docs/initiatives/legacy-feature-parity.md`: at-a-glance status per legacy app (`core`/`edge`/`grader`/`focus`/`croupier`/`sphinx`/`cabinet`/`pylon`/`concierge`/`lodge`/`ink`/`challenge`/`frontend`), by-audience capability tables (student/teacher/parent/admin/public), 7 known TODOs split by scope, and a retirement checklist. | The "Already ported" table lived in `CLAUDE.md` (routine prompt) — invisible to a reader browsing `docs/`. Pulling it into the initiatives folder gives it a stable URL, a status column to scan, and a place to record the gaps the routine table hand-waved over. Surfaced one concrete TODO from the M3-03 follow-up: `ADMINS` env-var wiring so `concierge` enquiry emails stop no-op'ing. |
