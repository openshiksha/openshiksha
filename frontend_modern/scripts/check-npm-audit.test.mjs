import { describe, expect, it } from 'vitest';
import { ALLOWLIST, BLOCKING_SEVERITIES, collectAdvisories, evaluateAudit } from './check-npm-audit.mjs';

/** Build a minimal `npm audit --json` shaped object. */
function auditReport(entries) {
  return {
    vulnerabilities: Object.fromEntries(
      entries.map(({ name, via }) => [name, { name, via }]),
    ),
  };
}

/** A root advisory as npm emits it (object member of `via`). */
function advisory({ id, name, severity = 'high', title = 'something bad' }) {
  return { source: 1, name, severity, title, url: `https://github.com/advisories/${id}` };
}

describe('collectAdvisories', () => {
  it('pulls out object `via` members and derives the id from the advisory url', () => {
    const report = auditReport([
      { name: 'react-router', via: [advisory({ id: 'GHSA-aaaa-bbbb-cccc', name: 'react-router' })] },
    ]);
    expect(collectAdvisories(report)).toEqual([
      {
        id: 'GHSA-aaaa-bbbb-cccc',
        severity: 'high',
        title: 'something bad',
        package: 'react-router',
        url: 'https://github.com/advisories/GHSA-aaaa-bbbb-cccc',
      },
    ]);
  });

  it('ignores string `via` members, which are transitive fallout rather than advisories', () => {
    const report = auditReport([
      { name: 'minimatch', via: ['brace-expansion'] },
      { name: 'filelist', via: ['minimatch'] },
    ]);
    expect(collectAdvisories(report)).toEqual([]);
  });

  it('de-duplicates one advisory reported against several packages', () => {
    const dupe = advisory({ id: 'GHSA-dupe-dupe-dupe', name: 'brace-expansion' });
    const report = auditReport([
      { name: 'brace-expansion', via: [dupe] },
      { name: 'minimatch', via: [dupe, 'brace-expansion'] },
    ]);
    expect(collectAdvisories(report).map((a) => a.id)).toEqual(['GHSA-dupe-dupe-dupe']);
  });

  it('tolerates an empty or malformed report', () => {
    expect(collectAdvisories({})).toEqual([]);
    expect(collectAdvisories(null)).toEqual([]);
  });
});

describe('evaluateAudit', () => {
  const allowlist = [{ id: 'GHSA-alwd-alwd-alwd', package: 'known', reason: 'r', review: 'later' }];

  it('does not block on an allowlisted advisory', () => {
    const report = auditReport([
      { name: 'known', via: [advisory({ id: 'GHSA-alwd-alwd-alwd', name: 'known' })] },
    ]);
    const { blocking, allowed } = evaluateAudit(report, allowlist);
    expect(blocking).toEqual([]);
    expect(allowed.map((a) => a.id)).toEqual(['GHSA-alwd-alwd-alwd']);
  });

  it('blocks on an advisory that is not allowlisted', () => {
    const report = auditReport([
      { name: 'other', via: [advisory({ id: 'GHSA-nope-nope-nope', name: 'other' })] },
    ]);
    const { blocking } = evaluateAudit(report, allowlist);
    expect(blocking.map((a) => a.id)).toEqual(['GHSA-nope-nope-nope']);
  });

  it('ignores advisories below the blocking severity', () => {
    const report = auditReport([
      { name: 'low-risk', via: [advisory({ id: 'GHSA-lowl-lowl-lowl', name: 'low-risk', severity: 'moderate' })] },
    ]);
    const { blocking, allowed } = evaluateAudit(report, allowlist);
    expect(blocking).toEqual([]);
    expect(allowed).toEqual([]);
  });

  it('blocks on critical as well as high', () => {
    const report = auditReport([
      { name: 'bad', via: [advisory({ id: 'GHSA-crit-crit-crit', name: 'bad', severity: 'critical' })] },
    ]);
    expect(evaluateAudit(report, allowlist).blocking).toHaveLength(1);
    expect([...BLOCKING_SEVERITIES]).toEqual(['high', 'critical']);
  });

  it('reports an allowlist entry that no longer matches anything as stale', () => {
    const { stale } = evaluateAudit(auditReport([]), allowlist);
    expect(stale.map((e) => e.id)).toEqual(['GHSA-alwd-alwd-alwd']);
  });

  it('passes cleanly on a report with no vulnerabilities', () => {
    const { blocking, allowed } = evaluateAudit({ vulnerabilities: {} }, []);
    expect(blocking).toEqual([]);
    expect(allowed).toEqual([]);
  });
});

describe('ALLOWLIST', () => {
  it('documents a reason and a removal condition for every entry', () => {
    for (const entry of ALLOWLIST) {
      expect(entry.id, 'entry needs a GHSA id').toMatch(/^GHSA-/);
      expect(entry.package, `${entry.id} needs a package`).toBeTruthy();
      expect(entry.reason.length, `${entry.id} needs a substantive reason`).toBeGreaterThan(40);
      expect(entry.review, `${entry.id} needs a removal condition`).toBeTruthy();
    }
  });

  it('has no duplicate ids', () => {
    const ids = ALLOWLIST.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
