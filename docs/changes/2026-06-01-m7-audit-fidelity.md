# Cabinet fidelity audit command + DoD regression guard

## Summary

Adds `audit_cabinet_fidelity` — a read-only management command that asserts the
Cabinet Data Fidelity initiative's cross-cutting **Definition of Done** as
enforceable metrics, plus a pytest that fails if any regress. This converts the
DoD from a one-off manual check into a standing invariant so a future re-import
can't silently undo the fidelity work.

## Classification

**New / test-coverage.**

## What changed

### Command — `apps/core/management/commands/audit_cabinet_fidelity.py`
Scopes all checks to the cabinet corpus (`tags__name__startswith="cabinet:"`)
and reports four metrics (each should be 0):

| Metric | Defect it catches | Closed by |
|---|---|---|
| `wrong_widget` | subpart with blank/invalid `subpart_type` | M7-03 |
| `legacy_tokens` | un-converted `_{x}_` / literal `#{img}#` token in any rendered field | M7-06 + token conversion |
| `taxonomy_placeholders` | cabinet question still on `Imported Subject/Chapter %` | M7-09 / mapping |
| `tag_cardinality` | cabinet tag attached to ≠ 1 Question | M7-05 |

`--strict` exits non-zero when any metric is out of bounds (CI guard). Read-only;
queries are scoped to cabinet tags so it never touches hand-authored content.

### Test — `apps/core/tests/test_cabinet_fidelity_audit.py`
Seeds the cabinet fixture via the importer (with the name mapping), asserts the
audit is all-green, then mutates one row (blank `subpart_type`; injected `#{}#`
leak) and asserts it flags — including the `SystemExit` under `--strict`.

Full backend suite green.

## Migration notes

None.

## Closing gate (follow-up, needs the Docker/Postgres stack)

Per the daily plan, after PRs 1–5 merge, re-run
`python manage.py import_cabinet_questions --source <cabinet>/questions` against
the seed/dev DB to materialise M7-06 inline images and per-subpart types on the
real corpus, then `python manage.py audit_cabinet_fidelity --strict` and confirm
it exits green. That step requires the dev Postgres (not connected in the build
environment), so it's the one remaining follow-on to declare the initiative
"✅ Complete".

## Next steps

- Run the closing-gate re-import + `--strict` audit on the dev stack.
- M7-11 (interactive widget) remains as the additive follow-on (not part of the
  original DoD).
