# M7-03 (remaining) — Question list filter parity

**Classification:** Fix.

## Summary
Two correctness bugs in the `/api/v1/questions/` list endpoint, both surfaced
by the Question Bank UI's growing reliance on it:

1. **Search returned duplicates.** `search_fields` joins through
   `subparts__question_text` and `tags__name`, so a question with several
   matching subparts (or several matching tags) appeared once per match.
2. **Grade filter mismatched.** `?standard=<N>` filtered `standard_id=N` —
   only correct when a Standard's PK happened to equal its number. The Browse
   endpoint (#194) already moved to `standard__number`; this brings the
   QuestionBank endpoint in line.

## Files changed
- `backend/openshiksha/apps/api/views/core.py` — `QuestionViewSet.get_queryset`
  ends with `.distinct()` and matches `standard__number` for the Grade filter.
- `backend/openshiksha/apps/api/tests/test_question_list_filters.py` — new
  regression tests (4) covering subpart-join dedup, tag-join dedup, standard-
  number filter, and combined search+standard.

## Verification
- New tests: 4/4 pass.
- Full api test suite: 167/167 pass (no other test depended on the buggy
  behaviour).
- `python manage.py check` clean.

## What's left in M7-03
- Assignment-list filtering: currently the student `AssignmentList` groups by
  status only (overdue / due-soon / upcoming / completed) — no UI filter
  controls exist. If product wants a "filter by subject room / status" pass on
  the student or teacher assignment list, it would be a small follow-up.

## Next
M2-02 mobile nav polish.
