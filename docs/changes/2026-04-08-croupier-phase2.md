# Croupier Phase 2 — Variable Substitution — 2026-04-08

## Summary

Implements deterministic variable substitution for numeric and fill-blank questions. Teachers write `{{a}}x + {{b}} = {{c}}` once; each student sees their own seeded values. The grader re-derives the same values at grading time to evaluate expression-based correct answers.

## Classification

**Improve** — Port from legacy Croupier with cleaner architecture. No Cabinet dependency, no `eval()` security risk.

## Legacy Reference

`croupier/` in repo root. Legacy implementation:
- Fetched variable definitions from Cabinet (external HTTP service)
- Evaluated correct-answer expressions via raw Python `eval()` — security risk
- Tightly coupled to Cabinet's question format, impossible to test without Cabinet running

## What's Different from Legacy

| Legacy | Modern |
|--------|--------|
| Variable definitions in Cabinet | `variable_constraints` JSONField on `QuestionSubpart` — no external service |
| Raw `eval()` on expression strings | `safe_eval_expr` via `ast.parse` + operator whitelist — zero security risk |
| No authoring preview for teachers | (Future: auto-detect `{{var}}` tokens in `CreateQuestionPage`) |
| Not testable without Cabinet running | Fully unit-testable, seedable in `seed_demo_data` |
| Single seed namespace for all croupier ops | Distinct namespaces: Phase 1 `"{student}:{subpart}"`, Phase 2 `"{student}:{subpart}:vars"` |

## Technical Details

### Model

`QuestionSubpart.variable_constraints` — nullable JSONField:

```json
{
  "a": {"min": 2, "max": 9, "integer": true},
  "b": {"min": 1, "max": 20, "integer": true},
  "c": {"min": 10, "max": 50, "integer": true}
}
```

Also supported: `"integer": false, "decimals": 2` for float variables.

### Croupier functions (Phase 2)

- `_make_var_seed(student_id, subpart_id)` — sha256 hash of `"{student_id}:{subpart_id}:vars"` mod 2^32
- `sample_variable_values(constraints, student_id, subpart_id)` — deterministically samples values from each variable's range
- `substitute_variables(text, variable_values)` — replaces `{{var}}` tokens
- `substitute_variables_for_student(question_text, options, constraints, student_id, subpart_id)` — returns `(text, options, variable_values)`
- `safe_eval_expr(expr, variable_values)` — ast-based arithmetic evaluator; supports `+`, `-`, `*`, `/`, `**`, unary `-`

### Question-serve time (serializer)

`QuestionSubpartStudentSerializer.to_representation` applies:
1. Phase 2 variable substitution (if `variable_constraints` is set)
2. Phase 1 MCQ shuffle (if `options` is non-empty)

Both can apply to the same subpart. Seed namespaces ensure no interference.

### Grading time (tasks.py)

`_grade_subpart` now accepts `variable_constraints`. For numeric questions:
- Re-derives the same variable values using `sample_variable_values` (same seed = same result)
- If `correct_answer["answer"]` contains `{{`, evaluates via `safe_eval_expr`
- Compares with tolerance `abs(submitted - expected) < 0.01`
- Falls back to direct comparison for non-expression constants

### Demo data

`seed_demo_data` adds a 4th question:
- Text: `"Solve: {{a}}x + {{b}} = {{c}}. Find x."`
- `correct_answer`: `{"type": "numeric", "answer": "({{c}} - {{b}}) / {{a}}"}`
- `variable_constraints`: `a ∈ [2,9]`, `b ∈ [1,20]`, `c ∈ [10,50]` (all integers)

## Tests Written

**`test_croupier_phase2.py`** — 18 tests:

- `TestSampleVariableValues` (5 tests): determinism, student isolation, bounds enforcement, integer/float types
- `TestSafeEvalExpr` (6 tests): arithmetic correctness, rejection of function calls and name nodes, power, unary negation, plain constants
- `TestSubstituteVariablesForStudent` (3 tests): question text substitution, option substitution, no-op with no constraints
- `TestGradingNumericVariableQuestion` (4 tests): correct variable answer grades 1.0, wrong grades 0.0, non-variable numeric unaffected, seed namespaces are distinct

**Total**: 272 backend tests pass (was 254 before). Coverage: 88.62%.

## Migration Notes

Migration `0004_questionsubpart_variable_constraints.py` — adds nullable JSONField. No data migration. Safe to apply without downtime (no default required on existing rows).

## Next Steps

1. **Question authoring UI** — `CreateQuestionPage.tsx` should auto-detect `{{var}}` tokens as teachers type and show a variable constraints input panel (min/max/integer per variable, with sample substitution preview)
2. **Teacher Question-Mistake Analytics** — `QuestionMistakeViewSet` + "Hardest Questions" section in `TeacherAssignmentDetailPage`
3. **Student Learning Path Page** — `/student/learning-path` using the existing `LearningPath` API

## PR

https://github.com/openshiksha/openshiksha/pull/73
