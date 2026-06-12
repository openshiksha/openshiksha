# Language Access — i18n (English / हिंदी) across the product

**Status:** 🟢 Active (promoted 2026-06-11)
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
| LA-1 | i18n foundation: `src/shared/i18n/` provider + `useT()` + en/hi locale files + navbar/drawer language switcher + `<html lang>` sync + pilot migration (auth pages) | ⬜ planned 2026-06-11 |
| LA-2 | `User.preferred_language` + profile API + ProfilePage selector + login seeding | ⬜ planned 2026-06-11 |
| LA-3 | Student core loop chrome in Hindi: dashboard, assignment list/detail, panels | ⬜ planned 2026-06-11 |
| LA-4 | AI content in the reader's language: explanations + parent-summary language wiring (+ regenerate-on-language-change) | ⬜ planned 2026-06-11 |
| LA-5 | Key-parity CI guard (Vitest), Hindi glossary, parent + registration chrome | ⬜ planned 2026-06-11 |
| LA-6 | Teacher surfaces chrome (dashboard panels, create-assignment, grading queue) | ⬜ |
| LA-7 | Localized transactional emails (grading complete, remedial, due reminders, parent weekly) honoring `preferred_language` | ⬜ |
| LA-8 | Number/date formatting via `Intl` keyed to locale (dates on cards, "due in X days") | ⬜ |
| LA-9 | Third-language pilot (one regional language on one surface) proving the framework scales | ⬜ |
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

## Progress Ledger (append-only)

| Date | Increment | PR | Learning |
|---|---|---|---|
| 2026-06-11 | Initiative promoted; LA-1..5 planned as the first batch ([plan](../daily-plans/2026-06-11-plan.md)) | — | The backend has spoken Hindi since the explanations feature shipped, but no UI could ask for it — wire `language` params into the product the day they ship, or they sit dark like the `/ai/` groups did. |
