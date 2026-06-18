# Code scanning (CodeQL SAST)

`.github/workflows/codeql.yaml` runs GitHub's CodeQL static analysis on the
code **we** write — backend (`python`) and frontend (`javascript-typescript`)
in parallel via a matrix.

## Why it exists / how it layers

The repo already scans **dependencies** at three points:

| Check | Where | Scope |
|-------|-------|-------|
| `pip-audit` | `security` job, `ci-cd.yaml` | backend requirements vs known CVEs |
| `npm audit` | `frontend` job, `ci-cd.yaml` | frontend lockfile vs known CVEs |
| `dependency-review-action` | `dependency-review.yaml` | CVEs/licenses a PR newly adds |

All three find flaws in **third-party packages**. None of them look at our own
source. CodeQL fills that gap: it flags injection (SQLi, command/path),
unsafe deserialization, XSS, cleartext logging of secrets, SSRF, and similar
patterns in first-party code.

## When it runs

- Every push and PR to `modernization` / `qa` / `prod`.
- A weekly scheduled full scan (Mondays 06:17 UTC) so advisories that land in
  CodeQL's query packs are caught even on quiet branches.

`build-mode: none` — Python and TS are interpreted, so CodeQL builds its
database straight from source with no compile step. The
`security-and-quality` query suite is used for broader coverage than the
default security-only suite.

## Where results show up

Findings appear under **Security ▸ Code scanning** as SARIF and annotate the
offending PR. CodeQL alerts do **not** hard-fail the merge by default; to gate
merges on them, enable *required* code-scanning results in branch protection
(see [`branch-protection.md`](branch-protection.md)).

## Triaging a finding

1. Open the alert in the Code scanning tab; CodeQL shows the data-flow path.
2. Fix the root cause if it's a true positive.
3. If it's a false positive or accepted risk, dismiss with a reason in the UI,
   or scope it out with an inline `# codeql[rule-id]` style suppression /
   a `.github/codeql/codeql-config.yml` `query-filters` entry. Record any
   standing ignore here, alongside the rationale, mirroring how the
   `security` job documents its `--ignore-vuln` entries.
