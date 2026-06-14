# LA-9d — Marathi parent surface + AI-language fallback guard

**Date:** 2026-06-13
**Classification:** New (content) + small backend
**Initiative:** Language Access — depends on LA-9b (#350)

## Summary

Translates the **parent dashboard** into Marathi (~20 keys) and adds an explicit
**backend AI-language fallback guard** so a `preferred_language='mr'` user never
sends an unsupported language to the LLM: AI-*generated* content (explanations,
parent summaries) falls back to English, and the persisted `language` field
reflects that. UI chrome is Marathi; AI/authored content stays a separate track
(initiative principle 1).

## What changed

### Frontend (content)
- **`locales/mr.ts`** — added the `parent.` cluster (~20 keys): dashboard title /
  description, no-children + no-progress empty states, grade labels, overview,
  tabs, status chips, due/overdue dates, questions-practised counts. Placeholders
  (`{name}`, `{grade}`, `{count}`, `{date}`) preserved.
- *Note:* the profile/settings page has no i18n keys yet (it doesn't call `t()`),
  so there was no profile chrome to translate in this PR.

### Backend (guard)
- **`ai/llm_client.py`** — new `AI_SUPPORTED_LANGUAGES = ("en", "hi")` +
  `resolve_ai_language(language)` which maps any other locale (e.g. `mr`, `fr`,
  `None`, `""`) to `"en"`. Applied at the top of `generate_explanation` and
  `generate_parent_summary` so the **prompt** is always built for a supported
  language (no blank/garbled instruction) regardless of caller.
- **`ai/tasks.py`** — `generate_subpart_explanation` and the parent-summary task
  normalize `language` through `resolve_ai_language` before generating **and**
  before persisting, so the stored `SubpartExplanation.language` /
  `ParentProgressSummary.language` matches the language the content was produced
  in. The weekly batch passes `parent.preferred_language` straight into the
  (now-guarded) task.
- **Email layer was already safe:** `core.emails.format_email_string` already
  falls back to English for an unknown language — verified, no change needed.

## Tests

- Backend: parametrized `resolve_ai_language` (`mr/fr/None/"" → en`, `en/hi`
  unchanged); `generate_explanation` + `generate_parent_summary` build the
  prompt for English when `mr` is requested (provider env cleared → stub path).
  → 10 passed; parent-intelligence suite → 49 passed (no regression).
- Frontend: renders Marathi parent-dashboard chrome (`parent.title`).
  `vitest run src/shared/i18n` → 39 passed; `tsc`/`eslint` clean; build green
  (`mr-*.js` lazy chunk 12 kB).

## Next steps

LA-9e: Marathi glossary + a coverage-report test + the LA-9 close-out (flip the
backlog row, update STATUS.md).
