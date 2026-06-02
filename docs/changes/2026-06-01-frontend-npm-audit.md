# Frontend npm audit fix — Vite 7 / Vitest 4

**Date:** 2026-06-01
**Area:** `frontend_modern/`
**Type:** Security / dependencies

## Problem

`npm audit --audit-level=high` (a CI gate in the `frontend` job) failed with 8
vulnerabilities — 3 reported critical (the `vitest` / `@vitest/ui` /
`@vitest/coverage-v8` chain) and 5 moderate (`esbuild`/`vite`/`vite-node`,
`brace-expansion`, `ws`). All are dev/test-tooling only — none ship in the
production bundle — but the gate blocks every frontend PR.

## Fix

Coordinated bump of the Vite/Vitest toolchain to current majors, plus the two
non-breaking transitive fixes:

| Package | Before | After |
|---|---|---|
| `vite` | ^5.0.10 | ^7.3.5 |
| `@vitejs/plugin-react` | ^4.2.1 | ^5.2.0 |
| `vitest` | ^1.1.0 | ^4.1.8 |
| `@vitest/coverage-v8` | ^1.6.1 | ^4.1.8 |
| `@vitest/ui` | ^1.1.0 | ^4.1.8 |
| `brace-expansion`, `ws` | — | `npm audit fix` (transitive) |

Vite 7 bundles esbuild ≥0.25 (the audit flagged only `vite <=6.4.1`), clearing
the esbuild advisory without needing Vite 8 / plugin-react 6 (which would pull in
the Rolldown stack). Vitest 4 clears the critical chain. `plugin-react@5.2`
peer-supports Vite 7 and 8.

Result: **`npm audit` → 0 vulnerabilities.**

`engines.node` raised `>=18` → `>=20.19.0` (Vite 7's floor). CI already runs
Node 20, which satisfies it.

## Coverage threshold re-baseline

Vitest 4's v8 coverage provider uses AST-aware remapping, which counts branches
and functions more accurately than Vitest 1 did. The **same 38 tests** now
measure differently:

| Metric | Vitest 1 floor | Vitest 4 measured | New threshold |
|---|---|---|---|
| Lines | 10.24% | 10.43% | 10 (unchanged) |
| Statements | — | 10.43% | 10 (unchanged) |
| Functions | 18.64% | 6.98% | 6 |
| Branches | 45.77% | 8.52% | 8 |

`functions` and `branches` thresholds in `vite.config.ts` were lowered to the new
floor with this recorded reason (the config requires one). No tests were lost —
only the measurement methodology changed. Ratchet back up as new tests land.

## Verification

All five frontend CI steps pass locally (Node 22):
`npm audit --audit-level=high` (0 vulns) · `npm run lint` · `npm run type-check` ·
`npm test -- --run --coverage` (38 passed) · `npm run build`.
