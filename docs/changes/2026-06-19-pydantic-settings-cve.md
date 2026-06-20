# 2026-06-19 — Security: bump pydantic-settings 2.14.1 → 2.14.2 (GHSA-4xgf-cpjx-pc3j)

## What

Bumped the backend pin in `backend/requirements.txt`:

```diff
-pydantic-settings==2.14.1
+pydantic-settings==2.14.2
```

A patch-level bump within the 2.14 line. No code changes — `pydantic-settings`
is consumed only through the existing settings/config plumbing, and the bump
keeps the same `pydantic` (2.10.5) compatibility floor as 2.14.1.

## Why

A new advisory landed in the pip-audit / GitHub advisory database and started
**failing the `security` (pip-audit) job in `ci-cd.yaml` on every push to
`modernization`** — including docs-only commits (first observed on the
`beacf336` plan commit, run 27859816141). The pipeline was red purely on this:

```
Found 1 known vulnerability in 1 package
Name              Version ID                  Fix Versions
pydantic-settings 2.14.1  GHSA-4xgf-cpjx-pc3j 2.14.2
```

- **GHSA-4xgf-cpjx-pc3j** (MODERATE): `NestedSecretsSettingsSource` follows
  symlinks **outside** `secrets_dir`, enabling local file read and bypassing the
  `secrets_dir_max_size` guard. Vulnerable range `>= 2.12.0, < 2.14.2`; fixed in
  `2.14.2`.

Bumping to the patched release clears the advisory and turns the pipeline green
again. Unlike the two long-standing documented ignores in the `security` job
(twisted `GHSA-grgv-6hw6-v9g4`, pyjwt `PYSEC-2025-183` — both have no usable
stable fix), this one has a clean patch fix, so we take the fix rather than
adding another `--ignore-vuln`.

## Risk

Very low. Patch-level dependency bump with a real upstream fix; no application
code is touched. The full CI gate (lint, typecheck, **security**, test,
frontend, e2e) re-runs on this PR and confirms the audit is clean and nothing
regressed.
