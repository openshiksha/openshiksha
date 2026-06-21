# LA-7 — transactional emails in the recipient's language

**Date:** 2026-06-12
**Classification:** Improve
**Initiative:** [Language Access — i18n en/हिंदी](../initiatives/2026-language-access.md) (LA-7)

## Summary

All four transactional emails (remedial assigned, grading complete, due-date
reminder, parent weekly summary) now render in the recipient's
`preferred_language`. Also fixes a real bug: the Monday parent-summary batch
(`enqueue_weekly_parent_summaries`) never passed a language, so Hindi-preferring
parents always received English AI narratives.

## What changed and why

- **`core/emails.py`** — per-module string catalog (`_STRINGS["en"/"hi"]`) +
  `format_email_string(catalog, user, key, **vars)` helper reading
  `user.preferred_language` with English fallback (missing key/language never
  crashes — an untranslated email beats a broken one). No gettext/.po — same
  no-heavyweight-machinery principle as the frontend module.
- **`ai/emails.py`** — parent weekly summary chrome (subject, greeting, intro,
  needs-attention/home-activity prefixes, CTA, footer) through the same helper.
  The AI `summary_text` passes through verbatim — it is already generated in
  the requested language.
- **`ai/tasks.py`** — `enqueue_weekly_parent_summaries` passes
  `language=parent.preferred_language` to `generate_parent_progress_summary`
  (the dark-language bug).

Dates inside emails (e.g. "May 27", week ranges) stay English-formatted —
locale-aware date formatting is LA-8.

## Tests

- `test_email_notifications.py` +5 (`TestEmailLocalization`): Hindi
  remedial/grading/reminder subject+body, English default unchanged, unknown
  language falls back to English.
- `test_parent_intelligence.py` +3: enqueue passes the parent's language;
  Hindi chrome dispatch (first direct test of `notify_parent_weekly_summary`
  delivery content); English default. Existing fans-out assertion updated for
  the new `language` kwarg.
- 69 targeted tests green; full suite + `manage.py check` green; no model
  changes → no migration.

## Next steps

LA-6a (teacher dashboard chrome) lands next; LA-8 will localize dates/numbers
including inside these emails.
