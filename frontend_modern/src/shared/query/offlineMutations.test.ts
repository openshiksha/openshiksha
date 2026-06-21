import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, MutationObserver, onlineManager, type Mutation } from '@tanstack/react-query';

// Mock the axios client so the mutationFns hit no real network.
vi.mock('@/api/client', () => ({
  apiClient: {
    patch: vi.fn(),
    post: vi.fn(),
  },
}));

import { apiClient } from '@/api/client';
import {
  registerSubmissionMutationDefaults,
  shouldDehydrateSubmissionMutation,
  SUBMISSION_PATCH_KEY,
  type PatchSubmissionVars,
} from './offlineMutations';

const patch = apiClient.patch as unknown as ReturnType<typeof vi.fn>;

const submission = { id: 1, assignment: 7, answers: { '1': '2' }, completion: 0.5, score: null };

beforeEach(() => {
  vi.clearAllMocks();
  onlineManager.setOnline(true);
});

afterEach(() => {
  onlineManager.setOnline(true);
});

describe('shouldDehydrateSubmissionMutation (offline-write allowlist)', () => {
  const fake = (isPaused: boolean, key: readonly unknown[] | undefined) =>
    ({ state: { isPaused }, options: { mutationKey: key } }) as unknown as Mutation;

  it('persists only PAUSED submission mutations', () => {
    expect(shouldDehydrateSubmissionMutation(fake(true, ['submission', 'patch']))).toBe(true);
    expect(shouldDehydrateSubmissionMutation(fake(true, ['submission', 'create']))).toBe(true);
  });

  it('never persists a running (non-paused) submission mutation', () => {
    expect(shouldDehydrateSubmissionMutation(fake(false, ['submission', 'patch']))).toBe(false);
  });

  it('never persists a non-submission mutation, even when paused', () => {
    expect(shouldDehydrateSubmissionMutation(fake(true, ['auth', 'login']))).toBe(false);
    expect(shouldDehydrateSubmissionMutation(fake(true, undefined))).toBe(false);
  });
});

describe('offline submission mutation queue', () => {
  it('pauses (not fails) when offline and replays the keyed mutationFn on reconnect', async () => {
    const queryClient = new QueryClient();
    registerSubmissionMutationDefaults(queryClient);

    // Go offline; the first offlineFirst attempt rejects with a network error and
    // the retry is then paused (durable) rather than the mutation failing.
    onlineManager.setOnline(false);
    patch.mockRejectedValue(new Error('Network Error'));

    const observer = new MutationObserver<typeof submission, Error, PatchSubmissionVars>(queryClient, { mutationKey: SUBMISSION_PATCH_KEY });
    const result = observer.mutate({ id: 1, data: { answers: { '1': '2' }, completion: 0.5 } });

    // The mutation is captured as paused (queued), not errored — and the allowlist
    // picks it up. offlineFirst runs the first attempt, then pauses the retry while
    // offline (after the retry backoff), so allow time for that transition.
    await vi.waitFor(
      () => {
        const m = queryClient.getMutationCache().getAll()[0];
        expect(m?.state.isPaused).toBe(true);
      },
      { timeout: 4000, interval: 50 },
    );
    const paused = queryClient.getMutationCache().getAll()[0];
    expect(shouldDehydrateSubmissionMutation(paused)).toBe(true);

    // Reconnect: the server is reachable now; resume drives the keyed mutationFn.
    patch.mockResolvedValue({ data: submission });
    onlineManager.setOnline(true);
    await queryClient.resumePausedMutations();

    await expect(result).resolves.toEqual(submission);
    expect(patch).toHaveBeenLastCalledWith('/submissions/1/', {
      answers: { '1': '2' },
      completion: 0.5,
    });

    // Default onSuccess reconciled the cache from the server response (no closure).
    expect(queryClient.getQueryData(['submission', 7])).toEqual(submission);
  });

  it('registers a rehydration-safe keyed mutationFn (no inline closure needed)', async () => {
    const queryClient = new QueryClient();
    registerSubmissionMutationDefaults(queryClient);
    patch.mockResolvedValue({ data: submission });

    // A mutation created with only a mutationKey (as a rehydrated paused mutation
    // would be) still resolves its function from the registered defaults.
    const observer = new MutationObserver<typeof submission, Error, PatchSubmissionVars>(queryClient, { mutationKey: SUBMISSION_PATCH_KEY });
    await observer.mutate({ id: 1, data: { answers: {} } });

    expect(patch).toHaveBeenCalledWith('/submissions/1/', { answers: {} });
  });
});
