# Language Access — i18n (English / हिंदी / मराठी) across the product

**Status:** 🟢 Active — LA-1..9 shipped; only LA-10 (authored-content
translation, blocked on product design) remains (promoted 2026-06-11)
**Owner surface:** whole product (frontend chrome, user preference, AI content language, emails)

---

## North Star

A Hindi-medium student or parent can use OpenShiksha's core loop — log in, see
the dashboard, work an assignment, read an AI explanation, read the weekly
parent summary — **entirely in Hindi**, switch languages in one tap, and have
the choice follow them across devices. English stays the default; Hindi is the
first proof that the platform can speak its users' language, and the framework
must make a third (regional) language a content task, not an engineering task.

This serves the core mission directly: OpenShiksha is a K-12 platform for
India, where most students and parents are more comfortable in Hindi or a
regional language than in English. The AI backend already speaks Hindi
(`language="hi"` on `/ai/explanations/` and parent summaries) — the product
just never lets anyone ask for it.

## Principles

1. **UI chrome translates; authored content does not.** Question text, options,
   teacher announcements, and names render as authored. We translate the
   product's own words (buttons, headings, statuses, empty states) and steer
   *AI-generated* content (explanations, parent summaries) via the existing
   `language` parameters. Content translation is a separate, later workflow.
2. **No heavyweight dependency.** The entry chunk is 93 kB with a 160 kB CI
   guard (Performance Budget initiative — defended). For two locales with
   simple interpolation, a tiny in-house module (`src/shared/i18n/`, ~2 kB)
   beats adding i18next (~45 kB raw). Revisit only if plural rules or RTL
   force the issue.
3. **English is the fallback, never a blank.** A missing Hindi key renders the
   English string (with a dev-mode `console.warn`). Key parity between locale
   files is CI-enforced so drift is caught at PR time.
4. **Real Hindi, K-12 register.** Devanagari script; everyday register a
   Std 6 student or a non-English-speaking parent reads comfortably. Domain
   words that Indian classrooms use in English (Assignment, Submit, Dashboard)
   are transliterated, not academically translated — see the Glossary. Flag
   translations for human review in the PR description; never block on it.
5. **The preference is the user's, and it travels.** Stored on the User row
   (`preferred_language`), editable from the profile page and the navbar
   switcher, seeded into the session at login, overridable per device via
   localStorage. `<html lang>` always reflects the active locale (a11y/screen
   readers).

## Foundation / Scaffold (what exists today, 2026-06-11)

- **Backend, ready:** `llm_client` prompts support `language == "hi"`
  (Devanagari instruction) for answer explanations and parent summaries;
  `/ai/explanations/generate/` and the parent-summary generate action accept
  `language`; `AnswerExplanation.language` field exists
  (`ExplanationLanguage` choices). `useParentSummary.ts` already types
  `language: 'en' | 'hi'`.
- **Backend, missing:** no `preferred_language` on `User`; explanation
  uniqueness is `(student, subpart, submission)` with no language dimension;
  emails are English-only.
- **Frontend, missing:** no i18n module, no locale files, no switcher; every
  string is hardcoded English.
- **V2 design system:** Fraunces + Inter — Inter covers Devanagari poorly;
  the i18n module ships with a Devanagari-capable font stack fallback
  (e.g. `"Noto Sans Devanagari", system-ui` appended for `lang="hi"`) —
  verify rendering, don't assume.

## Backlog (session-sized increments)

| ID | Increment | Status |
|----|-----------|--------|
| LA-1 | i18n foundation: `src/shared/i18n/` provider + `useT()` + en/hi locale files + navbar/drawer language switcher + `<html lang>` sync + pilot migration (auth pages) | ✅ 2026-06-11 [#308](https://github.com/openshiksha/openshiksha/pull/308) |
| LA-2 | `User.preferred_language` + profile API + ProfilePage selector + login seeding | ✅ 2026-06-11 [#309](https://github.com/openshiksha/openshiksha/pull/309) |
| LA-3 | Student core loop chrome in Hindi: dashboard, assignment list/detail, panels | ✅ 2026-06-11 [#310](https://github.com/openshiksha/openshiksha/pull/310) |
| LA-4 | AI content in the reader's language: explanations + parent-summary language wiring (+ regenerate-on-language-change) | ✅ 2026-06-11 [#311](https://github.com/openshiksha/openshiksha/pull/311) |
| LA-5 | Key-parity CI guard (Vitest), Hindi glossary, parent + registration chrome (+ home page, added per user request) | ✅ 2026-06-11 [#312](https://github.com/openshiksha/openshiksha/pull/312) + LA-5b |
| LA-6 | Teacher surfaces chrome (dashboard panels, create-assignment, build-problem-set, grading queue, authoring previews, question bank, rubric, widget gallery, versions, classroom code, CreateQuestionPage) | ✅ 2026-06-13 — 6a–6d [#318](https://github.com/openshiksha/openshiksha/pull/318)–[#321](https://github.com/openshiksha/openshiksha/pull/321); 6e [#323](https://github.com/openshiksha/openshiksha/pull/323)/[#324](https://github.com/openshiksha/openshiksha/pull/324)/[#325](https://github.com/openshiksha/openshiksha/pull/325)/[#326](https://github.com/openshiksha/openshiksha/pull/326) |
| LA-7 | Localized transactional emails (grading complete, remedial, due reminders, parent weekly) honoring `preferred_language` | ✅ 2026-06-12 [#314](https://github.com/openshiksha/openshiksha/pull/314) |
| LA-8 | Number/date formatting via `Intl` keyed to locale (dates on cards, "due in X days") | ✅ 2026-06-13 [#322](https://github.com/openshiksha/openshiksha/pull/322) |
| LA-9 | Third-language pilot (one regional language on one surface) proving the framework scales | ✅ 2026-06-13 — 9a [#349](https://github.com/openshiksha/openshiksha/pull/349) (N-locale registry + pilot-coverage parity); Marathi 9b [#350](https://github.com/openshiksha/openshiksha/pull/350) / 9c [#351](https://github.com/openshiksha/openshiksha/pull/351) / 9d [#352](https://github.com/openshiksha/openshiksha/pull/352) / 9e [#353](https://github.com/openshiksha/openshiksha/pull/353) |
| LA-10 | Authored-content translation workflow (question text) — needs product design, do not start without promotion | ⬜ |

## Definition of Done (every increment)

- Build/lint/types/tests green; entry-chunk budget guard still passes.
- en/hi key parity holds (no key in one file missing from the other).
- New/changed UI keeps V2 tokens and works at mobile widths; `<html lang>`
  correct; Devanagari actually renders (spot-check, don't assume the font).
- Hindi strings follow the Glossary register; PR description lists new Hindi
  strings under a "translation review" heading for human eyes.
- Ledger row appended here; STATUS.md headline updated when the initiative moves.

## Continuous Improvement pool (pick one per session)

- Extract a hardcoded string cluster someone missed into the locale files.
- Tighten the glossary with terms encountered this session.
- Add a missing-key dev warning improvement or parity-test edge.
- Audit one surface's Devanagari rendering/overflow (Hindi strings run ~20% longer).
- Replace an ad-hoc date/number rendering with the `Intl` helper (post LA-8).

## Glossary (Hindi register — grow as you go)

| English | Hindi (UI) | Note |
|---|---|---|
| Assignment | असाइनमेंट | transliterate — classroom English |
| Submit | जमा करें | |
| Dashboard | डैशबोर्ड | transliterate |
| Practice | अभ्यास | |
| Score | स्कोर | transliterate |
| Due date | अंतिम तिथि | |
| Chapter | अध्याय | |
| Streak | स्ट्रीक | transliterate — product term |
| Review | दोहराव | SRS context |
| Hint | संकेत | |
| Explanation | व्याख्या | |
| Teacher / Student / Parent | शिक्षक / विद्यार्थी / अभिभावक | |
| Sign in / Log in | साइन इन करें / लॉग इन करें | transliterate — universal |
| Username / Password | यूज़रनेम / पासवर्ड | transliterate |
| Register / Create account | रजिस्टर करें / खाता बनाएँ | |
| Overdue | समय निकल गया | "अतिदेय" too formal for K-12 |
| Pending | बाकी है | |
| Progress | प्रगति | |
| Grace day | ग्रेस ✓ | product term, transliterate |
| Classroom join code | क्लासरूम जॉइन कोड | transliterate — classroom English |
| Insights | इनसाइट्स | transliterate — product term |
| Learning path | लर्निंग पाथ | transliterate — product term |
| Question bank | प्रश्न बैंक | transliterate "bank" — classroom English |
| Problem set | समस्या सेट | transliterate "set" |
| Rubric | रूब्रिक | transliterate — classroom English |
| Version | संस्करण | |
| Snapshot | स्नैपशॉट | transliterate — product term |
| Difficulty | कठिनाई | |
| Subpart / Part | उपभाग / भाग | |
| Variable / Constraint | चर / बाधा | |
| Widget | विजेट | transliterate — product term |
| Draft | ड्राफ़्ट | transliterate |

## Glossary (Marathi register — LA-9 pilot, grow as you go)

Marathi (मराठी) shipped as the LA-9 third-language pilot (anonymous journey +
student core loop + parent dashboard). Same register philosophy as Hindi:
everyday Maharashtra K-12 Marathi; classroom-English/product terms are
transliterated, not academically translated. **Flagged for human review.**

| English | Marathi (UI) | Note |
|---|---|---|
| Assignment | असाइनमेंट | transliterate — classroom English |
| Submit | सादर करा | |
| Dashboard | डॅशबोर्ड | transliterate |
| Practice | सराव | |
| Score | गुण | |
| Due date | मुदत | |
| Chapter | अध्याय | |
| Streak | मालिका | |
| Review | पुनरावलोकन | SRS context |
| Explanation | स्पष्टीकरण | |
| Teacher / Student / Parent | शिक्षक / विद्यार्थी / पालक | |
| Sign in / Log in | साइन इन करा | transliterate — universal |
| Username / Password | युझरनेम / पासवर्ड | transliterate |
| Register / Create account | नोंदणी करा / खाते तयार करा | |
| Overdue | मुदत संपलेली | |
| Pending | प्रलंबित | |
| Progress | प्रगती | |
| Grade (class) | इयत्ता | |
| Question bank | प्रश्नपेढी | |
| Insights | माहिती | |
| Learning path | शिक्षण मार्ग | |
| Grace day | सवलत ✓ | product term |

## Progress Ledger (append-only)

| Date | Increment | PR | Learning |
|---|---|---|---|
| 2026-06-11 | Initiative promoted; LA-1..5 planned as the first batch ([plan](../daily-plans/2026-06-11-plan.md)) | — | The backend has spoken Hindi since the explanations feature shipped, but no UI could ask for it — wire `language` params into the product the day they ship, or they sit dark like the `/ai/` groups did. |
| 2026-06-11 | LA-1 — i18n foundation, EN\|हिं switcher, login pilot. Entry chunk 93→96.5 kB; hi dict is its own lazy chunk. | [#308](https://github.com/openshiksha/openshiksha/pull/308) | A no-provider English fallback in `useI18n` (instead of throwing) kept every existing component test wrapper-free — the migration cost stays linear in surfaces, not in test files. |
| 2026-06-11 | LA-2 — `preferred_language` end-to-end; precedence device > profile > en; switcher PATCHes profile when authenticated. | [#309](https://github.com/openshiksha/openshiksha/pull/309) | Seeding from the profile must NOT write localStorage — otherwise the first login would mint a device override and later profile changes would never propagate. |
| 2026-06-11 | LA-3 — student core loop chrome in Hindi (~60 keys); date-fns `hi` locale for relative dates, kept out of the entry chunk. | [#310](https://github.com/openshiksha/openshiksha/pull/310) | "3 दिन में" beats "in 3 days में" — localizing the chrome without the dates reads worse than not localizing at all; date-fns ships a tree-shakeable hi locale, no Intl machinery needed yet (LA-8). |
| 2026-06-11 | LA-4 — explanations + parent summaries generate in the reader's language; regenerate-in-place affordance on language mismatch. | [#311](https://github.com/openshiksha/openshiksha/pull/311) | The backend already regenerated in place (`update_or_create` with `language` in defaults) — the "gap" was purely frontend. Read the task before writing backend code; two pinning tests were all the backend needed. |
| 2026-06-11 | LA-5 — runtime parity guard (key sets + `{var}` placeholder drift); home page + all registration pages in Hindi (home added per user request); parent dashboard chrome (LA-5b). | [#312](https://github.com/openshiksha/openshiksha/pull/312) + LA-5b | The anonymous journey (home → register → login) is the highest-leverage Hindi surface: it's what a non-English-speaking parent sees before anyone can help them. |
| 2026-06-12 | LA-7 — all four transactional emails render in the recipient's `preferred_language`; fixed the Monday parent-summary batch that never passed a language. | [#314](https://github.com/openshiksha/openshiksha/pull/314) | Email is a second render target with no `useT` context — factor the locale dictionaries so the same keys serve both React and the server-side email templates. |
| 2026-06-13 | LA-6a–6d — teacher dashboard + 8 insight panels, create-assignment, build-problem-set, AI grading queue in Hindi (~270 keys). Shipped as a stacked PR chain. | [#318](https://github.com/openshiksha/openshiksha/pull/318)–[#321](https://github.com/openshiksha/openshiksha/pull/321) | Rich sentences recompose as whole `{var}` interpolations, not concatenated fragments — Hindi word order differs, so a sentence split across JSX nodes can't be translated faithfully. Plural via `*One`/`*Many` key pairs. |
| 2026-06-13 | LA-8 — locale-aware `formatDate`/`formatNumber`/`useFormat` via the platform `Intl` API. Invalid dates pass through; numbers use Indian grouping with Latin digits (K-12 product call). | [#322](https://github.com/openshiksha/openshiksha/pull/322) | `Intl` is built into the browser — solving date/number formatting once cost **zero** entry-chunk bytes, and the helper now back-fills 6a–d and carries into LA-9. Relative dates stay on date-fns `hi` (LA-3); this is for absolute dates only. |
| 2026-06-13 | LA-6e-1 — authoring preview & edit-safety chrome (AssignmentSnapshotPreview, ResyncAssignmentModal, EditSafetyBanner, ProblemSetPreviewPage). EditSafetyBanner's free-text `noun` prop became a typed `subject` so the headline is a proper localized sentence. | [#323](https://github.com/openshiksha/openshiksha/pull/323) | A free-text prop carrying a half-sentence ("this problem set") can't be localized at the call site — lift the whole sentence into the key and let the component pick by an enum prop. |
| 2026-06-13 | LA-6e-2 — question bank (+ add-to-set sheet), QuestionPreviewPanel, RecordResponsePanel (rubric authoring), WidgetGalleryPanel (~115 keys). Added `localizedTypeLabel(t, type)` for the six question types. | [#324](https://github.com/openshiksha/openshiksha/pull/324) | Parallel locale-file PRs off `modernization` all collide at the same anchor — each needs a trivial `merge modernization` before it lands. Stacking them (base each on the prior) would have avoided it; noted for LA-9. |
| 2026-06-13 | LA-6e-3 — version history (+ diff panel) & classroom join-code in Hindi. First 6e slice to consume LA-8 `useFormat().formatDate` for version timestamps. | [#325](https://github.com/openshiksha/openshiksha/pull/325) | The LA-8 helper paid off immediately — a hardcoded `toLocaleString('en-IN', …)` became one `formatDate` call that respects the active locale. |
| 2026-06-13 | LA-6e-4 — CreateQuestionPage (1131 lines, the last English-only teacher surface) in Hindi (~95 `cqp.*` keys); added the page's first test file. **Closes LA-6.** | [#326](https://github.com/openshiksha/openshiksha/pull/326) | Page-local `cqp.type*` labels instead of reusing the in-flight LA-6e-2 `qtype.*` kept this PR independent — cross-PR key reuse would have forced a merge order. LaTeX/`{{token}}` hints survive because `t()` without vars is a no-op on `{…}`. |
| 2026-06-13 | LA-9a — generalized the binary `en\|hi` machine into `locales/registry.ts` (one entry per locale drives switcher/loader/`Intl`/parity) + a complete-vs-pilot coverage contract. Pure refactor, zero behavior change for en/hi. | [#349](https://github.com/openshiksha/openshiksha/pull/349) | A string-literal `Locale` union `satisfies`-checked against the registry array keeps `t()` keys statically typed *and* makes a new language a one-line union edit. An explicit loader map beat a template `import(`./${code}`)` for reliable Vite chunk-splitting. |
| 2026-06-13 | LA-9b — registered Marathi (मरा); switcher became EN\|हिं\|मरा with **no switcher edit** (the registry payoff). `mr.ts` shipped as a pilot subset (anonymous journey, ~45 keys) + backend `preferred_language` choice. | [#350](https://github.com/openshiksha/openshiksha/pull/350) | The whole engineering surface for language #3 was one registry entry + a union widening — everything else was content. Proof the North Star clause ("a content task, not an engineering task") is met. |
| 2026-06-13 | LA-9c — Marathi student core loop (~72 keys). date-fns 4.x ships no `mr` locale, so mr relative dates fall back to English while absolute dates localize via `Intl` `mr-IN`. | [#351](https://github.com/openshiksha/openshiksha/pull/351) | A pilot locale exposes the language gap in AI surfaces: the explanation "re-explain" affordance had to compare against `toAiLanguage(locale)`, not the raw locale, or it shows forever for a locale whose AI content is English. |
| 2026-06-13 | LA-9d — Marathi parent dashboard (~20 keys) + backend `resolve_ai_language()` guard (mr→en) so AI explanations/summaries never carry an unsupported language; persisted `language` matches generated content. | [#352](https://github.com/openshiksha/openshiksha/pull/352) | The email layer already fell back to English (`format_email_string`) — the only real gap was AI *generation*. Centralizing the fallback in one helper kept prompt + stored field consistent for any caller. |
| 2026-06-13 | LA-9e — `coverage.test.ts` pilot-coverage report (mr at 137/764 = 17.9%, with a regression floor) + Marathi glossary. **Closes LA-9.** | [#353](https://github.com/openshiksha/openshiksha/pull/353) | The framework is proven for N languages: language #4 (a non-Devanagari stress test like Tamil) is now config + content + one font-stack entry, no code change. Only LA-10 (authored-content translation, blocked on product design) remains. |
