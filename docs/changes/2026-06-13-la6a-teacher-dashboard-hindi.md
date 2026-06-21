# LA-6a — teacher dashboard + insight panels in Hindi

**Date:** 2026-06-13
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-6)

## Summary

The teacher dashboard shell and its eight insight panels now render in the
reader's `preferred_language` via the in-house i18n module. This is the first
slice of **LA-6** (teacher surfaces chrome); create-assignment/authoring (6b)
and the AI grading queue (6c) follow as separate PRs.

## What changed and why

Replaced hardcoded English UI strings with `t(...)` calls across the teacher
dashboard and its panels, and added the matching `teacher.*` keys to both
locale files. Hindi strings are genuine domain translations (विषय रूम, प्रॉब्लम
सेट, अटक रहे, निपुण …), not transliterations.

Files touched (frontend only — no API/model changes):

- `TeacherDashboard.tsx` — title/subtitle, stat tiles, room + problem-set cards,
  empty states, join-code section, assignment list, action buttons.
- `NeedsAttentionPanel.tsx` — bucket chips. Bucket labels remain stable English
  identifiers (also used in `data-testid`s); only the user-facing chip text is
  localized via a typed `Record<string, LocaleKey>` map.
- `ClassHealthPanel.tsx`, `WeeklyReportPanel.tsx`, `InterventionsPanel.tsx`,
  `MisconceptionClustersPanel.tsx`, `AssignmentDraftsPanel.tsx`,
  `QuestionQualityPanel.tsx` — headings, table headers, status labels,
  loading/empty/error states, refresh controls.
- `locales/en.ts` + `locales/hi.ts` — ~150 new `teacher.*` keys across nine
  labelled sections. Count-bearing strings use `{count}`/`{submitted}`/`{total}`
  interpolation; placeholders are identical across locales (parity-guarded).

## Design / conventions

- No new dependency — same in-house module (`useT`, `LocaleKey`) as LA-1..5.
- Stable identifiers (bucket labels, testids) deliberately kept English so
  existing tests and data attributes are untouched.
- Key parity is tsc-enforced via `LocaleDict`; the runtime `parity.test.ts`
  additionally checks blank strings + `{var}` placeholder drift.

## Tests

- `npm run type-check` — clean (proves en↔hi key parity).
- `npm run lint` — clean.
- `vitest run src/shared/i18n` — 13 passed (key sets, blanks, placeholders).
- `vitest run src/features/teacher` — 131 passed (no regressions).
- `npm run build` — succeeds; entry bundle 115.72 kB (within the 160 kB budget).

## Next steps

- **LA-6b** — create-assignment / problem-set / question-authoring pages.
- **LA-6c** — AI grading queue (`/teacher/grading`).
- After 6c, LA-6 reaches Definition of Done and the Language Access initiative
  closes (LA-7 already shipped in #314).
