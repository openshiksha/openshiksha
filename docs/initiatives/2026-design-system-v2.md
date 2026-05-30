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
  - `primary` 50–900 (legacy blue) — **retained only so un-migrated pages keep
    rendering. New/migrated code must not use `primary`.**
  - `boxShadow`: `soft`, `card`, `lift` (warm-toned elevation).
  - `fontFamily`: `sans` (Inter), `display` (Fraunces).
  - `animation`: `fade-up`, `fade-in`, `float`.
- **Brand CSS layer** — `frontend_modern/src/index.css`: warm `body` base,
  Fraunces headings, and seed component classes (`.btn-brand`, `.btn-ghost`,
  `.os-card`, `.input-brand`, `.chalk-underline`, `.bg-paper`, `.bg-chalkboard`).
- **Seed component library** — `frontend_modern/src/shared/ui/`: `Logo`,
  `Button`, `Card`, `Badge`, a barrel `index.ts`, and a **conventions
  `README.md`** every session must follow when adding components.
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

### M1 — Foundation  *(mostly done in kickoff)*
- [x] `M1-01` Brand assets + favicon + fonts wired into `index.html`.
- [x] `M1-02` Token system in `tailwind.config.js` (brand, ink, shadows, motion).
- [x] `M1-03` Brand CSS layer in `index.css` (base + seed component classes).
- [x] `M1-04` Seed `ui/` library (Logo, Button, Card, Badge) + conventions README.
- [x] `M1-05` `/design` living showcase route.
- [ ] `M1-06` Add `Input`, `Badge` (severity variants), `Stat`, `SectionHeading`,
  `Skeleton`, `EmptyState` primitives to `ui/` + showcase.

### M2 — Global shell  *(every page inherits this — do first)*
- [x] `M2-01` Reskin **App Shell** (`AppShell` + `Navbar`): real `<Logo/>`, warm
  paper background, brand active-nav (chalk underline), warm user menu.
- [ ] `M2-02` Mobile nav polish: brand hamburger sheet, role chips, safe-area.
- [ ] `M2-03` Global states: branded `LoadingSpinner`, 404/NotFound, error
  boundary fallback, toast style.

### M3 — Auth & marketing  *(first impression; self-contained, low-risk)*
- [x] `M3-01` **Login** → chalkboard-left / paper-right brand layout (flagship).
- [ ] `M3-02` Register + Register-school + Register-open in the new language.
- [ ] `M3-03` Public **Enquire** page (prospective schools) — credible + warm.
- [x] `M3-04` **Home page** at `/` — legacy-inspired (chalkboard hero →
  Practice/Evaluate/Analyse → mission + teacher photo → "Start now" → features),
  new branding, legacy hero images, branded Login CTA. Logo links home everywhere.

### M7 — Functional parity & enrichment  *(HIGH PRIORITY — the frontend must do everything the legacy did, better)*

> Surfaced by reviewing the running app as `student_demo` (see
> `screenshots/questions-broken-before.png`). These are functional, not purely
> visual — but they are what "fully featured" means and gate real classroom use.
> If this milestone grows, graduate it to its own initiative.

- [ ] `M7-01` **Question content rendering — LaTeX + HTML.** Question/subpart text,
  options, and worked solutions ship as HTML containing LaTeX (`\(…\)`, `$…$`,
  `\over`, `\sqrt`, `\sqrt 3\over 2`). Today `QuestionCard` prints them as **raw
  text**. Render sanitised HTML + KaTeX (the stack already has `katex` +
  `react-katex`). Must cover inline + block math, MCQ options, and solutions.
- [ ] `M7-02` **Question variable substitution ("widgets").** Legacy/Cabinet
  questions embed templated variables — `{4*j}`, `{12*j}`, `{j*29}` — that must be
  computed into concrete per-attempt values (the legacy "croupier"/variable
  system). Today they render as raw `{…}`. Decide where realisation happens
  (backend realises per attempt vs. frontend) and implement so students see real
  numbers. Investigate the legacy interactive-widget question types and port any
  still in use.
- [ ] `M7-03` **List-page filtering / search / sort actually works.** Browse,
  Question Bank, assignment lists etc. have filter/search controls that don't
  filter. Wire them to the API query params (or client-side) so they work, with
  branded controls.
- [ ] `M7-04` **Feature-parity audit vs. legacy.** Walk the legacy app surface by
  surface; log every capability the modern frontend is missing into this backlog.
- [ ] `M7-05` **Fix `seed_demo_data` idempotency.** `Question.get_or_create`
  matches multiple rows (`MultipleObjectsReturned`) on re-seed; make the demo
  seed reliably re-runnable so reviewers always have clean question data.

### M4 — Product surfaces  *(one screen = one increment; highest daily use first)*
- [ ] `M4-01` Student Dashboard
- [ ] `M4-02` Parent Dashboard + **Parent Insights** (align with the shipped
  `AlertsPanel`/`HomeActivitiesPanel` styling)
- [ ] `M4-03` Teacher Dashboard
- [ ] `M4-04` Admin Dashboard + Classroom manage
- [ ] `M4-05` Assignment detail (student) + SRS drill
- [ ] `M4-06` Proficiency + Learning Path + Browse
- [ ] `M4-07` Teacher authoring (Create question / problem-set / assignment, Question bank)
- [ ] `M4-08` Profile / settings

### M5 — Mobile & responsive pass
- [ ] `M5-01` Bottom tab bar for primary roles on mobile.
- [ ] `M5-02` Per-surface responsive audit of migrated M4 pages.

### M6 — Hardening
- [ ] `M6-01` Accessibility audit (AA) across migrated surfaces.
- [ ] `M6-02` Retire the legacy `primary` (blue) token once no migrated code uses it.
- [ ] `M6-03` Visual-regression screenshots of `/design` + key pages.

> When M4 is the active milestone, **migrate the highest-traffic un-migrated page
> next.** A migrated page uses only `ui/` + tokens, has zero `primary`/`indigo`/
> `gray-50` references left, and is added to the screenshot set.

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
