# Remove "non-profit" from all user-facing copy

**Date:** 2026-06-11
**Classification:** Improve (copy)

## Summary

Removed every "non-profit" mention from user-facing surfaces, per request.
Replacement copy keeps each sentence coherent rather than leaving holes.

## What changed

Modern frontend:
- `HomePage.tsx` — hero eyebrow `Non-profit · CBSE · Classes 7–10` →
  `CBSE · Classes 7–10 · English & हिन्दी`; mission copy "a non-profit
  platform" → "a learning platform"; partnership copy "schools and
  non-profits" → "schools and educational organisations".
- `LoginPage.tsx` + `AuthLayout.tsx` — chalkboard-panel footer line
  `Non-profit · CBSE · English & हिन्दी` → `CBSE · Classes 7–10 · English & हिन्दी`.

Legacy landing (still served at the legacy root):
- `openshiksha/templates/index.html` — meta description + intro copy
  ("a non-profit education(al) platform" → "an education(al) platform");
  partnership paragraph ("educational non-profits and schools" →
  "educational organisations and schools").
- `openshiksha/static/js/index_translate.js` — the same two phrases inside
  the `#quick_intro` English translation string.

Verified with a repo-wide grep (`non-profit|nonprofit|non profit`,
case-insensitive): zero user-facing mentions remain.

## Tests

Frontend lint + tsc + build green; LoginPage suite passes (HomePage has no
test file — pure static copy).
