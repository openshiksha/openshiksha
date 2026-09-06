import { describe, expect, it } from 'vitest';
import {
  checkBudget,
  findEntryChunk,
  formatBytes,
  DEFAULT_BUDGET_BYTES,
} from './check-bundle-budget.mjs';

describe('findEntryChunk', () => {
  it('extracts the entry chunk path from a typical Vite index.html', () => {
    const html =
      '<!doctype html><html><head>' +
      '<script type="module" crossorigin src="/assets/index-ABC123.js"></script>' +
      '<link rel="modulepreload" crossorigin href="/assets/vendor-react-XYZ.js">' +
      '</head><body></body></html>';
    expect(findEntryChunk(html)).toBe('assets/index-ABC123.js');
  });

  it('handles single-quoted attributes', () => {
    const html = "<script type='module' src='/assets/index-Q.js'></script>";
    expect(findEntryChunk(html)).toBe('assets/index-Q.js');
  });

  it('throws when no entry script is present', () => {
    expect(() => findEntryChunk('<html><body>no script</body></html>')).toThrow();
  });
});

describe('formatBytes', () => {
  it('renders < 1 kB as bytes', () => {
    expect(formatBytes(512)).toBe('512 B');
  });
  it('renders >= 1 kB with two decimals of kB', () => {
    expect(formatBytes(1024)).toBe('1.00 kB');
    expect(formatBytes(160 * 1024)).toBe('160.00 kB');
  });
});

describe('checkBudget', () => {
  it('passes when the entry is under the budget', () => {
    const result = checkBudget({
      entryChunk: 'assets/index-AAA.js',
      sizeBytes: 100 * 1024,
      budgetBytes: 160 * 1024,
    });
    expect(result.ok).toBe(true);
    expect(result.message).toContain('OK');
    expect(result.message).toContain('assets/index-AAA.js');
    expect(result.message).toContain('headroom');
  });

  it('passes exactly at the budget (boundary)', () => {
    const result = checkBudget({
      entryChunk: 'assets/index-AAA.js',
      sizeBytes: 160 * 1024,
      budgetBytes: 160 * 1024,
    });
    expect(result.ok).toBe(true);
  });

  it('fails when the entry exceeds the budget and points at how to raise the ceiling', () => {
    const result = checkBudget({
      entryChunk: 'assets/index-BIG.js',
      sizeBytes: 200 * 1024,
      budgetBytes: 160 * 1024,
    });
    expect(result.ok).toBe(false);
    expect(result.message).toContain('FAIL');
    expect(result.message).toContain('assets/index-BIG.js');
    expect(result.message).toContain('over the');
    expect(result.message).toContain('DEFAULT_BUDGET_BYTES');
    expect(result.message).toContain('docs/perf/budget.md');
  });
});

describe('DEFAULT_BUDGET_BYTES', () => {
  it('is set to the documented 180 kB ceiling', () => {
    expect(DEFAULT_BUDGET_BYTES).toBe(180 * 1024);
  });
});
