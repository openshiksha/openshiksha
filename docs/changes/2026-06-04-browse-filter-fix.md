# M7-03 — Browse filter wiring (Grade selector)

**Classification:** Fix.

## Summary
The `BrowsePage` Grade dropdown sends a *standard number* (1..12), but the
backend's browse endpoint matched `standard_id=<number>`, which only worked by
accident when a standard's PK happened to equal its number. On any real
deployment with shuffled PKs the Grade filter silently returned an empty list
(or worse, the wrong chapters).

## Files changed
- `backend/openshiksha/apps/api/views/core.py` —
  `Question.browse_chapters` now filters by `standard__number=<number>`.
- `backend/openshiksha/apps/api/tests/test_browse_filter.py` — new regression
  test covering: standard-number filter, subject filter, combined filter,
  unfiltered fall-through.

## Verification
- New test file: 4/4 pass.
- Full api test suite: 163/163 pass.
- `python manage.py check` clean.

## Next
- M5-01 mobile bottom tab bar.
