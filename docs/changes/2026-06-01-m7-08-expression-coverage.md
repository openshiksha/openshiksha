# M7-08 — Importer `--report-unknowns` + expression-coverage triage

## Summary

Adds a **read-only** `--report-unknowns` flag to `import_cabinet_questions` that
walks every `{{...}}` token across all cabinet subparts and reports identifiers
that are neither declared sampled variables, allowlisted constants
(`_SAFE_CONSTS`), nor allowlisted functions (`_SAFE_FUNCS`). The flag writes
nothing to the DB. Triaging its output extended the croupier allowlist with a set
of safe, pure math helpers so the "unknown function" count collapses to a stable
residual that is purely a *data* issue (undeclared variables), not a missing
capability.

## Classification

**Improve** — makes the `safe_eval_expr` allowlist's coverage *observable*
instead of failing silently, and closes the gap for legitimate math helpers.

## Legacy files referenced

- `croupier/constraints.py` — original (unrestricted) Python `eval` of author
  expressions; modern `safe_eval_expr` replaced it with an AST allowlist.
- `cabinet/cabinet_api.py` — original token/expression render path.

## What changed

### `backend/openshiksha/apps/api/croupier.py`
- `_SAFE_CONSTS`: added `pi` / `e` aliases (alongside the existing Cabinet-author
  spellings `pi_val` / `e_val`).
- `_SAFE_FUNCS`: added pure, deterministic math helpers — `gcd`, `lcm`,
  `factorial`, `degrees`, `radians`, trig (`sin`/`cos`/`tan`/`asin`/`acos`/
  `atan`/`atan2`), logs (`log`, `ln`, `log10`, `log2`), `exp`, plus the value
  constructors `Fraction` (exact rationals) and `str` (used inside the legacy
  `Decimal(str(x))` idiom; `Decimal` is aliased to `float`).
- All additions are side-effect-free; no I/O, no mutation, no attribute access.
  The AST evaluator's existing guards (rejecting attribute access, non-allowlisted
  calls, comprehensions, dunder names) are reused unchanged.

### `backend/openshiksha/apps/core/management/commands/import_cabinet_questions.py`
- New `--report-unknowns` flag (read-only; early-returns after the scan).
- `_iter_expressions()` — yields every `{{...}}` inner expression from a converted
  subpart (`question_text`, `solution_text`, `hint_text`, option texts,
  `correct_answer.answer`).
- `_collect_unknown_names()` — parses each expression and returns `ast.Name` ids
  not covered by declared vars / `_SAFE_CONSTS` / `_SAFE_FUNCS`. Malformed
  expressions yield nothing (already reported elsewhere as conversion errors).
- `_report_unknowns()` — scans all containers, prints a frequency-sorted
  `name → count` table with an example token, plus scanned/skipped totals.

## Scan output against the real bank (646 containers)

Before allowlist extension: **17 distinct** unknown names (1841 occurrences).
After: **14 distinct** (1417 occurrences) — the resolved names were `str`,
`Fraction`, `ln`.

The 14 residual names are **all undeclared variables** referenced in expressions
but absent from those subparts' `variable_constraints` (`j`, `k`, `l`, `m`, `n`,
`o`, `o1`, `o2`, `l2`, `m1`, `i`, `a`, `b`, and `temp`). These leave their tokens
un-substituted at render time — a **content/data** defect, not an allowlist gap.
This is the stable residual the audit (PR 5) should track; it is out of scope for
this allowlist PR.

## Tests

`backend/openshiksha/apps/core/tests/test_cabinet_expr.py` (new, 16 tests):
- `_collect_unknown_names` classification (declared var / const / func / unknown /
  malformed / newly-allowlisted helpers).
- `_iter_expressions` collects tokens from every field.
- Extended allowlist present + evaluates (`gcd`, `factorial`, `pi`).
- `--report-unknowns` command writes nothing to the DB and prints a scan summary.

All 47 cabinet-expr + croupier tests pass; full suite 718 passed, 92.94% coverage.

## Migration notes

None — no schema change.

## Next steps

- PR 2: M7-06 inline-image extraction.
- The 14 undeclared-variable findings feed the PR 5 `audit_cabinet_fidelity`
  guard (un-substituted token detection).
