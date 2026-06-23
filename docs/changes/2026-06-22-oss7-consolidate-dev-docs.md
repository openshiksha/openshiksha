# 2026-06-22 — OSS-7: consolidate root dev docs under `docs/dev/`

**Summary.** Move the four loose dev guides off the repo root into `docs/dev/`
(kebab-cased, history preserved via `git mv`), add a `docs/dev/README.md` index,
and repoint every inbound hyperlink. The root now shows only the modern stack +
GitHub-special files.

**Classification.** Improve.

**Initiative.** Open-Source Readiness (Priority 1) — backlog item OSS-7.

## What changed

- `git mv` (history preserved), kebab-cased on the move:
  - `CHEAT_SHEET.md` → `docs/dev/cheat-sheet.md`
  - `GIT_STRATEGY.md` → `docs/dev/git-strategy.md`
  - `LOCAL_DEVELOPMENT.md` → `docs/dev/local-development.md`
  - `SETUP_MODERNIZATION.md` → `docs/dev/setup-modernization.md`
- New `docs/dev/README.md` — one-line index of each guide + cross-links to
  deploy / initiatives / contributing.
- Repointed every inbound hyperlink:
  - `README.md` — Quickstart link + the `## Documentation` block (added a
    "Developer guides" entry pointing at the new index).
  - `CONTRIBUTING.md` — local-development + git-strategy links.
  - `docs/dev/cheat-sheet.md` — its internal "Full guide" link.

The GitHub-special root files (`README`, `CONTRIBUTING`, `SECURITY`,
`CODE_OF_CONDUCT`, `LICENSE.md`) stay at root.

## Note on remaining grep hits

`grep` for the old uppercase filenames still matches **non-link** text: the
historical ASCII directory trees and `git add CHEAT_SHEET.md` / `cp` command
examples inside `git-strategy.md` and `setup-modernization.md` (these document a
one-time past migration), plus prose mentions in the ledger/plan docs. Those are
descriptive records, not navigable links, and were intentionally left intact. A
grep restricted to Markdown link syntax (`](…CHEAT_SHEET.md)` etc.) returns
**zero** results.

## Tests

- `grep -rnE "\]\(...(LOCAL_DEVELOPMENT|GIT_STRATEGY|CHEAT_SHEET|SETUP_MODERNIZATION).md\)"`
  across `*.md` → zero remaining old-root **links**.
- `git status` shows the four files as renames (history preserved).
- `pre-commit` green. Docs-only — no code references these paths, no CI impact.

## Next steps

OSS-10 (repo metadata + license badge) closes the batch and the initiative DoD.
