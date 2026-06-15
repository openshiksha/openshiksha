import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Query } from '@tanstack/react-query';
import type { PersistedClient } from '@tanstack/react-query-persist-client';

// In-memory stand-in for idb-keyval so the persister round-trips without a real
// IndexedDB (happy-dom has none).
const store = new Map<string, unknown>();
vi.mock('idb-keyval', () => ({
  get: vi.fn(async (k: string) => store.get(k)),
  set: vi.fn(async (k: string, v: unknown) => void store.set(k, v)),
  del: vi.fn(async (k: string) => void store.delete(k)),
}));

import {
  shouldPersistQueryKey,
  shouldDehydrateQuery,
  createIDBPersister,
} from './persist';

beforeEach(() => store.clear());

describe('shouldPersistQueryKey (offline-read allowlist)', () => {
  it('persists the student core-loop reads', () => {
    expect(shouldPersistQueryKey(['assignments'])).toBe(true);
    expect(shouldPersistQueryKey(['assignment', 7])).toBe(true);
    expect(shouldPersistQueryKey(['student', 'streak'])).toBe(true);
    expect(shouldPersistQueryKey(['srs', 'due'])).toBe(true);
  });

  it('persists only the student-facing AI sub-keys', () => {
    expect(shouldPersistQueryKey(['ai', 'recommendations'])).toBe(true);
    expect(shouldPersistQueryKey(['ai', 'practice-plan', 'today'])).toBe(true);
    // Teacher/analytics AI reads stay online-only.
    expect(shouldPersistQueryKey(['ai', 'weekly-report', 3])).toBe(false);
    expect(shouldPersistQueryKey(['ai', 'interventions', 3])).toBe(false);
  });

  it('never persists auth or other roles’ data', () => {
    expect(shouldPersistQueryKey(['auth'])).toBe(false);
    expect(shouldPersistQueryKey(['auth', 'me'])).toBe(false);
    expect(shouldPersistQueryKey(['admin', 'summary'])).toBe(false);
    expect(shouldPersistQueryKey(['parent', 'children'])).toBe(false);
    expect(shouldPersistQueryKey(['questions'])).toBe(false);
  });

  it('rejects non-string roots defensively', () => {
    expect(shouldPersistQueryKey([])).toBe(false);
    expect(shouldPersistQueryKey([42])).toBe(false);
  });
});

describe('shouldDehydrateQuery', () => {
  const makeQuery = (queryKey: unknown[], status: string): Query =>
    ({ queryKey, state: { status } }) as unknown as Query;

  it('persists only successful allowlisted queries', () => {
    expect(shouldDehydrateQuery(makeQuery(['assignments'], 'success'))).toBe(true);
    expect(shouldDehydrateQuery(makeQuery(['assignments'], 'pending'))).toBe(false);
    expect(shouldDehydrateQuery(makeQuery(['auth'], 'success'))).toBe(false);
  });
});

describe('createIDBPersister', () => {
  it('round-trips and removes a persisted client', async () => {
    const persister = createIDBPersister('test-key');
    const client = {
      timestamp: Date.now(),
      buster: 'v1',
      clientState: { mutations: [], queries: [] },
    } as PersistedClient;

    await persister.persistClient(client);
    expect(await persister.restoreClient()).toEqual(client);

    await persister.removeClient();
    expect(await persister.restoreClient()).toBeUndefined();
  });
});
