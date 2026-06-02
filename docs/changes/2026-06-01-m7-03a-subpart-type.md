# M7-03a — `QuestionSubpart.subpart_type` (backend)

## Summary

Restores **per-subpart answer typing**, which Cabinet had (each subpart stored
its own `type`: 1=mcq, 2=multi_select, 3=numeric, 4=fill_blank) but the modern
flat `Question.question_type` lost. Adds `QuestionSubpart.subpart_type`, a
`COMPOUND` summary type for `Question.question_type` when subparts are
heterogeneous, a data-migration backfill, importer wiring, serializer exposure,
and per-subpart grader dispatch.

## Classification

**Improve / Port** — faithfully ports legacy per-subpart typing onto the modern
schema and adds a `compound` summary affordance legacy never had.

## Legacy files referenced

- `cabinet/cabinet_api.py` — per-subpart `type` field.
- `croupier/` — type-driven render/grade behaviour.

## What changed

### Model — `apps/core/models.py`
- `QuestionType.COMPOUND = "compound"` — only ever set on `Question.question_type`,
  never on a single subpart.
- `QuestionSubpart.subpart_type` — `CharField(choices=QuestionType.choices,
  blank=True, default="")`. Blank = fall back to the parent question type
  (hand-authored rows that predate this field).

### Migration — `0016_questionsubpart_subpart_type_and_more.py`
- Schema: add `subpart_type`, alter `question_type` choices to include `compound`.
- Data (`RunPython`, reversible no-op): backfill `subpart_type` from
  `correct_answer["type"]` (idempotent — only fills blanks, never clobbers
  hand-authored rows), then recompute each `Question.question_type` —
  unanimous subpart type → that type, mixed → `compound`.

### Importer — `import_cabinet_questions.py`
- `convert_subpart` returns `subpart_type` (from the cabinet `type`).
- `_import_container` computes the question summary: unanimous subpart type, or
  `compound` when heterogeneous. New `compound` stat in the report line.

### Serializers — `apps/api/serializers/core.py`
- `subpart_type` added to `QuestionSubpartStudentSerializer` (student-facing — the
  field the frontend widget will dispatch on in M7-03b), `QuestionSubpartSerializer`
  (teacher/admin), and `QuestionSubpartWriteSerializer` (optional on create/update).

### Grader — `apps/core/tasks.py`
- Dispatch on `subpart.subpart_type or subpart.question.question_type` so each
  subpart of a compound question grades by its own type.

### Admin — `apps/core/admin.py`
- `subpart_type` added to the `QuestionSubpartInline` fields.

## Tests

- `test_import_cabinet.py`: every imported subpart has a non-blank `subpart_type`;
  Q1001 → `mcq`; new heterogeneous fixture Q1007 (mcq + numeric) → question
  `compound` while subparts keep their own types; homogeneous question keeps its
  type. Count assertions updated for the new fixture question.
- `test_grading_tasks.py`: `test_grade_submission_dispatches_per_subpart_type` —
  a `compound` question with an mcq subpart + a numeric subpart grades each
  correctly (proves the grader doesn't use the parent `compound` type).

Full backend suite: **713 passed, 92.84%**.

## Migration notes

- Backfill is idempotent and reversible (reverse is a safe no-op — values stay
  valid choices). Run `migrate` then the closing re-import to materialise types
  on the live corpus.

## Stacking

Branched off the M7-06 branch (both touch the same importer regions). The diff
includes M7-06 until [#127](https://github.com/openshiksha/openshiksha/pull/127)
merges; GitHub will narrow it automatically afterward.

## Next steps

- **PR 4 (M7-03b)**: frontend `QuestionCard` switches the input widget on
  `subpart.subpart_type` (depends on this PR's serialized field).
