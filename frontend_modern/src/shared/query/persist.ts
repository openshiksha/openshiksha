import { get, set, del } from 'idb-keyval';
import type { PersistedClient, Persister } from '@tanstack/react-query-persist-client';
import type { Query } from '@tanstack/react-query';

/**
 * MSO-4 — persist the React Query cache to IndexedDB so a student who loaded
 * their work online can re-open it offline (paired with the MSO-3 precached
 * shell). Three deliberate guardrails (initiative principle 2):
 *
 *  1. **Reads only.** Mutations are never dehydrated (`shouldDehydrateMutation`
 *     returns false) — restoring a stale mutation could double-submit.
 *  2. **No auth/token data.** The `auth` query family is never persisted; JWTs
 *     live in the auth store, not the query cache, but we exclude it defensively.
 *  3. **An explicit allowlist.** Only the student core-loop reads that are safe
 *     and useful offline are persisted, so we never bloat IndexedDB with teacher
 *     PII or large question banks.
 */

/** IndexedDB key under which the whole dehydrated client is stored. */
export const IDB_CACHE_KEY = 'os-react-query-cache';

/**
 * Bump when the persisted query *shape* changes across a deploy so old caches
 * are discarded rather than rehydrated into incompatible code. Combined with
 * `PersistQueryClientProvider`'s `buster`.
 */
export const CACHE_BUSTER = 'v1';

/** 24h — long enough for a persisted entry to survive between sessions. */
export const PERSIST_MAX_AGE = 1000 * 60 * 60 * 24;

/**
 * Root query-key segments that are safe + useful to read offline: the student
 * dashboard (assignments + streak), assignment detail, due-for-review (SRS),
 * and the student-facing AI reads. Everything else (auth, teacher/admin/parent
 * data, problem-set authoring) is left online-only.
 */
const OFFLINE_READABLE_ROOTS = new Set<string>([
  'assignments', // dashboard assignment list
  'assignment', // assignment detail
  'student', // streak
  'srs', // due-for-review + drill
]);

/** Student-facing sub-keys of the broad `ai` family worth caching offline. */
const OFFLINE_READABLE_AI = new Set<string>([
  'recommendations',
  'practice-plan',
  'learning-paths',
  'explanations',
]);

/**
 * The allowlist predicate. Exported for unit testing — given a query key,
 * returns whether its data should be persisted for offline reading.
 */
export const shouldPersistQueryKey = (queryKey: readonly unknown[]): boolean => {
  const root = queryKey[0];
  if (typeof root !== 'string') return false;
  if (root === 'auth') return false; // never persist auth/token-bearing reads
  if (root === 'ai') return OFFLINE_READABLE_AI.has(String(queryKey[1]));
  return OFFLINE_READABLE_ROOTS.has(root);
};

/** Only dehydrate successful queries on the allowlist. */
export const shouldDehydrateQuery = (query: Query): boolean =>
  query.state.status === 'success' && shouldPersistQueryKey(query.queryKey);

/** An idb-keyval-backed persister (≈1 kB; lazy). */
export const createIDBPersister = (idbKey: string = IDB_CACHE_KEY): Persister => ({
  persistClient: async (client: PersistedClient) => {
    await set(idbKey, client);
  },
  restoreClient: async () => await get<PersistedClient>(idbKey),
  removeClient: async () => {
    await del(idbKey);
  },
});
