/**
 * PERF-06 — Bundle-size budget guard.
 *
 * After `npm run build`, run this script to assert that the entry JS chunk
 * (the one referenced by dist/index.html as a top-level <script type="module">)
 * is at most BUDGET_BYTES. Exits non-zero with a clear diff when the budget is
 * blown — protecting the gains landed in PERF-01..PERF-04.
 *
 * To raise the ceiling deliberately: change BUDGET_BYTES in this file (or pass
 * --budget=<bytes> on the CLI), commit a baseline + budget bump in the same PR,
 * and call out the reason in docs/perf/budget.md.
 *
 * Exported helpers (`findEntryChunk`, `formatBytes`, `checkBudget`) are unit-
 * tested in check-bundle-budget.test.mjs.
 */
import { readFileSync, statSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// The entry chunk measures ~161 kB uncompressed / ~50 kB gzip (2026-09-06).
// Budget set with ~12% headroom over that to absorb routine feature growth
// without false-alarming every PR. Raise deliberately — see the raise-the-
// ceiling protocol and the history table in docs/perf/budget.md.
export const DEFAULT_BUDGET_BYTES = 180 * 1024;

/**
 * Find the entry JS chunk filename from `dist/index.html`.
 * Looks for `<script type="module" ... src="/assets/<name>.js"></script>`.
 */
export function findEntryChunk(indexHtml) {
  const match = indexHtml.match(
    /<script[^>]*type=["']module["'][^>]*src=["']\/?(assets\/[^"']+\.js)["']/i,
  );
  if (!match) {
    throw new Error(
      'Could not find an entry <script type="module" src="/assets/*.js"> in dist/index.html.',
    );
  }
  return match[1];
}

export function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  return `${(n / 1024).toFixed(2)} kB`;
}

/**
 * Pure budget check. Returns `{ ok, message }` so it's trivially unit-testable
 * without touching the file system.
 */
export function checkBudget({ entryChunk, sizeBytes, budgetBytes }) {
  if (sizeBytes <= budgetBytes) {
    return {
      ok: true,
      message:
        `[bundle-budget] OK — ${entryChunk} is ${formatBytes(sizeBytes)} ` +
        `(budget ${formatBytes(budgetBytes)}, headroom ` +
        `${formatBytes(budgetBytes - sizeBytes)}).`,
    };
  }
  const over = sizeBytes - budgetBytes;
  return {
    ok: false,
    message:
      `[bundle-budget] FAIL — ${entryChunk} is ${formatBytes(sizeBytes)}, ` +
      `over the ${formatBytes(budgetBytes)} budget by ${formatBytes(over)}.\n` +
      `To raise the ceiling: bump DEFAULT_BUDGET_BYTES in ` +
      `frontend_modern/scripts/check-bundle-budget.mjs, document why in ` +
      `docs/perf/budget.md, and ship the change as its own PR.`,
  };
}

function parseCliBudget(argv) {
  for (const arg of argv) {
    const m = arg.match(/^--budget=(\d+)$/);
    if (m) return Number(m[1]);
  }
  return undefined;
}

function main() {
  const distDir = resolve(__dirname, '..', 'dist');
  const indexPath = join(distDir, 'index.html');
  if (!existsSync(indexPath)) {
    console.error(
      `[bundle-budget] FAIL — ${indexPath} does not exist. Did you forget to run \`npm run build\` first?`,
    );
    process.exit(2);
  }
  const html = readFileSync(indexPath, 'utf8');
  const entryRel = findEntryChunk(html);
  const entryAbs = join(distDir, entryRel);
  if (!existsSync(entryAbs)) {
    // Defensive — the hashed name from index.html should always resolve.
    console.error(
      `[bundle-budget] FAIL — entry chunk ${entryRel} referenced by index.html does not exist on disk.\n` +
        `assets/ contents: ${readdirSync(join(distDir, 'assets')).join(', ')}`,
    );
    process.exit(2);
  }
  const { size } = statSync(entryAbs);
  const budgetBytes = parseCliBudget(process.argv) ?? DEFAULT_BUDGET_BYTES;
  const result = checkBudget({ entryChunk: entryRel, sizeBytes: size, budgetBytes });
  console.log(result.message);
  process.exit(result.ok ? 0 : 1);
}

// Only execute when run as a script (not when imported for tests).
// `process.argv[1]` is the resolved entry path on all platforms; we just look
// at its basename rather than comparing URLs (Windows vs POSIX path encodings
// have bitten us here before).
const entryBasename = (process.argv[1] ?? '').replace(/\\/g, '/').split('/').pop();
if (entryBasename === 'check-bundle-budget.mjs') {
  main();
}
