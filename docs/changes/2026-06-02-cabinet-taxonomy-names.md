# Cabinet taxonomy — proper subject/chapter names baked into the importer

## Summary

`import_cabinet_questions` now produces **proper subject and chapter names by
default** instead of `Imported Subject/Chapter N` placeholders. A curated
mapping (`apps/core/data/cabinet_taxonomy.json`) is bundled and used as the
default whenever `--mapping` is not supplied. This closes the
`taxonomy_placeholders` metric of the Cabinet Data Fidelity DoD.

## Classification

**Improve** — removes the long-standing external-mapping dependency for naming
(P8 originally created placeholders "to be renamed later in Django admin"; M7-09
inference matched 0/51 against `ncert_toc.json`).

## What changed

### `apps/core/data/cabinet_taxonomy.json` (new)
Curated names inferred from cabinet question content cross-referenced with the
NCERT Class 7–11 syllabus:
- **Subjects** keyed by cabinet `subject_id`: 1=Mathematics, 2=Science,
  3=Physics, 4=Chemistry, 5=Biology.
- **Chapters** keyed by the **composite** `"<standard>:<subject_id>:<chapter_id>"`.
  This is required because cabinet `chapter_id` is **reused across
  standards/subjects** — e.g. id `1` is "Algebraic Expressions and Identities"
  in std 8 but "Sequences and Series" in std 11; id `44` is Physics-Thermo
  (subject 3) vs Chemistry-Thermo (subject 4); id `39` is a statistics set in
  std 9 but "Coordinate Geometry" in std 10. All 51 chapters across the corpus
  are named.

### `import_cabinet_questions.py`
- `_DEFAULT_TAXONOMY_PATH` → the bundled file.
- `_load_mapping(None)` now loads the bundled default (was: empty map). An
  explicit `--mapping` still overrides it entirely.
- `_resolve_taxonomy` resolves a chapter by composite key first, then a flat
  `<chapter_id>` (legacy / test-fixture format), then the placeholder.

## Naming caveat

A handful of cabinet "chapters" are mixed-topic practice sets rather than clean
NCERT chapters; those are named by dominant/representative topic (e.g. std 8
`3` → "Number Systems and Operations", `17` → "Practical Geometry"). Names are
distinct per cabinet chapter_id so no two cabinet chapters collapse into one
(which would re-introduce the M7-05 tag collision). Names can still be refined
in Django admin without re-import.

## Closing gate — VALIDATED GREEN on the real corpus

Run on the dev Postgres against the full openshiksha-cabinet clone (clean import):

```
$ python manage.py import_cabinet_questions --source <cabinet>/questions
imported=646 updated=0 skipped=2 new_subjects=0 new_chapters=0 images=137 stems=0 inline_images=1 compound=138

$ python manage.py audit_cabinet_fidelity --strict
cabinet questions: 646  subparts: 1741
  wrong_widget           0
  legacy_tokens          0
  taxonomy_placeholders  0
  tag_cardinality        0
DoD audit: all green.        (exit 0)
```

A second import reports `imported=0 updated=646` — **idempotent**.

**Residual:** `images=138` (137 sibling + 1 inline) is below the plan's hoped
≥500; per the daily plan that image-count gap is the only acceptable follow-up
and does not block the DoD audit (which is green). The 2 skipped questions are
cabinet `type:5` (unsupported, pre-existing).

### Migration note (re-import over an *already-populated* placeholder DB)

The M7-05 cabinet tag is scoped by chapter **PK**, so renaming chapters (new PKs)
on an existing placeholder DB makes a re-import create new rows instead of
updating (observed once during this transition). On a clean DB, or any DB already
carrying the proper names, imports are idempotent. To migrate an old placeholder
DB: delete cabinet-tagged questions + orphaned `Imported %` taxonomy, then
re-import (as done to validate this gate). A future hardening could key the tag
on cabinet source ids rather than DB PKs.

## Tests

`test_cabinet_taxonomy.py` (5): bundled file exists; `_load_mapping(None)` loads
proper subjects + composite chapter keys; explicit `--mapping` overrides; a
no-mapping import of a real-id fixture (std 11 / subj 3 / chap 44) yields
subject "Physics" + chapter "Thermodynamics" with zero placeholders. Existing
`test_import_cabinet.py` (placeholder + flat-mapping behaviour) still passes.

## Next steps

- With the audit green, Cabinet Data Fidelity can be marked ✅ Complete in
  STATUS.md (image-count follow-up tracked separately).
