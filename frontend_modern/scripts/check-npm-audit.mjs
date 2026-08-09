/**
 * npm audit gate with a documented advisory allowlist.
 *
 * Replaces a bare `npm audit --audit-level=high` in CI. Behaviour is identical
 * — fail on any high/critical advisory — except that advisories listed in
 * ALLOWLIST below are reported but do not fail the build.
 *
 * Why this exists: `npm audit` has no `--ignore <id>` flag, so the only way to
 * accept a specific advisory is to filter its output. The backend security job
 * already does exactly this via `pip-audit --ignore-vuln <id>` (see the
 * `security` job in .github/workflows/ci-cd.yaml); this brings the frontend
 * gate to parity instead of leaving CI permanently red.
 *
 * Rules for adding an entry:
 *   1. There must be no upgrade path that actually fixes it today.
 *   2. Record WHY it is not exploitable here, and what unblocks removal.
 *   3. Open a tracking issue and put its number in `review`.
 * Entries are meant to be temporary. Anything not listed still fails the build.
 *
 * Exported helpers (`collectAdvisories`, `evaluateAudit`) are unit-tested in
 * check-npm-audit.test.mjs.
 */
import { execFileSync } from 'node:child_process';

/** Severities that fail the build, mirroring `--audit-level=high`. */
export const BLOCKING_SEVERITIES = new Set(['high', 'critical']);

// Empty is the goal state: every advisory currently has a real upgrade path, so
// nothing needs accepting. Keep it that way — prefer fixing over adding here.
export const ALLOWLIST = [];

/**
 * Flatten `npm audit --json` into the distinct advisories behind it.
 *
 * In the audit report each entry under `vulnerabilities` has a `via` array whose
 * object members are root advisories and whose string members are just the names
 * of other vulnerable packages (transitive fallout). Only the objects carry an
 * advisory id, so those are what we gate on — this collapses the long cascade
 * npm prints (minimatch, filelist, jake, ejs, workbox-build, ...) back down to
 * the handful of real advisories underneath.
 */
export function collectAdvisories(auditJson) {
  const byId = new Map();
  for (const vuln of Object.values(auditJson?.vulnerabilities ?? {})) {
    for (const via of vuln.via ?? []) {
      if (typeof via === 'string' || !via?.url) continue;
      const id = via.url.split('/').pop();
      if (!byId.has(id)) {
        byId.set(id, { id, severity: via.severity, title: via.title, package: via.name, url: via.url });
      }
    }
  }
  return [...byId.values()];
}

/**
 * Split advisories into blocking vs. allowed. Pure, so it is trivially testable
 * without shelling out to npm.
 */
export function evaluateAudit(auditJson, allowlist = ALLOWLIST) {
  const allowedIds = new Set(allowlist.map((e) => e.id));
  const relevant = collectAdvisories(auditJson).filter((a) => BLOCKING_SEVERITIES.has(a.severity));
  return {
    blocking: relevant.filter((a) => !allowedIds.has(a.id)),
    allowed: relevant.filter((a) => allowedIds.has(a.id)),
    // An allowlist entry that no longer matches anything is stale — surface it
    // so the list gets pruned instead of quietly accumulating.
    stale: allowlist.filter((e) => !relevant.some((a) => a.id === e.id)),
  };
}

function runAudit() {
  // `npm audit` exits non-zero whenever it finds anything, so a non-zero exit is
  // expected and the JSON we want is still on stdout.
  try {
    return execFileSync('npm', ['audit', '--json'], { encoding: 'utf8', shell: process.platform === 'win32' });
  } catch (err) {
    if (err.stdout) return err.stdout;
    throw err;
  }
}

function main() {
  const { blocking, allowed, stale } = evaluateAudit(JSON.parse(runAudit()));

  for (const a of allowed) {
    const entry = ALLOWLIST.find((e) => e.id === a.id);
    console.log(`[npm-audit] ALLOWED ${a.id} (${a.package}, ${a.severity}) — ${entry.review}`);
  }
  for (const e of stale) {
    console.log(`[npm-audit] STALE allowlist entry ${e.id} (${e.package}) no longer matches — remove it.`);
  }

  if (blocking.length === 0) {
    console.log(
      `[npm-audit] OK — no unaccepted high/critical advisories ` +
        `(${allowed.length} allowlisted, see frontend_modern/scripts/check-npm-audit.mjs).`,
    );
    return;
  }

  console.error(`[npm-audit] FAIL — ${blocking.length} unaccepted high/critical advisory/advisories:`);
  for (const a of blocking) {
    console.error(`  - ${a.id} ${a.package} (${a.severity}): ${a.title}`);
    console.error(`    ${a.url}`);
  }
  console.error(
    `\nFix by upgrading the affected dependency. If there is genuinely no upgrade path, ` +
      `add a documented entry to ALLOWLIST in frontend_modern/scripts/check-npm-audit.mjs ` +
      `explaining why it is not exploitable here and what unblocks its removal.`,
  );
  process.exit(1);
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith('check-npm-audit.mjs')) {
  main();
}
