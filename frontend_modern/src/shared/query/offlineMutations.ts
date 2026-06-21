import type { Mutation, QueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Submission } from '@/types/index';

/**
 * MSO-7 — offline mutation queue foundation.
 *
 * Batch 1 made the student core loop survive a dropped connection for *reads*
 * (precached shell + persisted React Query cache). This wires the *write* half:
 * the student's submission auto-saves and final submit become keyed mutations
 * with `networkMode: 'offlineFirst'`, so when the network is down they **pause**
 * (durably persisted to IndexedDB) instead of failing, and replay automatically
 * when connectivity returns — even across a full reload.
 *
 * Two design constraints make a *rehydrated* paused mutation replayable:
 *
 *  1. **The `mutationFn` must not be a closure.** A mutation restored from
 *     IndexedDB has no component context, so its function is looked up by
 *     `mutationKey` from `setMutationDefaults` — registered here, before the
 *     persister restores the client (see `main.tsx`).
 *  2. **Cache reconciliation lives in the default `onSuccess`.** A replayed
 *     mutation has no live observer, so the `setQueryData`/invalidation that
 *     keeps the UI honest must run from the default, deriving everything it needs
 *     from the server response (never a captured variable).
 *
 * MSO-6 made the server idempotent, so an at-least-once replay of these is safe.
 */

/** Keyed mutation for an in-progress auto-save / final submit PATCH. */
export const SUBMISSION_PATCH_KEY = ['submission', 'patch'] as const;
/** Keyed mutation for creating the (online-first) submission row. */
export const SUBMISSION_CREATE_KEY = ['submission', 'create'] as const;

export interface PatchSubmissionVars {
  id: number;
  data: Partial<Pick<Submission, 'answers' | 'completion' | 'submitted_at'>>;
}

const patchSubmissionFn = async ({ id, data }: PatchSubmissionVars): Promise<Submission> => {
  const response = await apiClient.patch<Submission>(`/submissions/${id}/`, data);
  return response.data;
};

const createSubmissionFn = async (assignmentId: number): Promise<Submission> => {
  const response = await apiClient.post<Submission>('/submissions/', { assignment: assignmentId });
  return response.data;
};

/**
 * Register the keyed submission mutation defaults on a client. MUST be called
 * before `PersistQueryClientProvider` restores the cache, so a rehydrated paused
 * mutation can resolve its `mutationFn` by key.
 */
export function registerSubmissionMutationDefaults(queryClient: QueryClient): void {
  queryClient.setMutationDefaults(SUBMISSION_PATCH_KEY, {
    mutationFn: patchSubmissionFn as (vars: unknown) => Promise<Submission>,
    networkMode: 'offlineFirst',
    retry: 3,
    onSuccess: (updated: Submission) => {
      // Derive the assignment from the response — never a closure — so this also
      // runs correctly when a rehydrated mutation replays with no live observer.
      queryClient.setQueryData(['submission', updated.assignment], updated);
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });

  queryClient.setMutationDefaults(SUBMISSION_CREATE_KEY, {
    mutationFn: createSubmissionFn as (vars: unknown) => Promise<Submission>,
    networkMode: 'offlineFirst',
    retry: 3,
    onSuccess: (created: Submission) => {
      queryClient.setQueryData(['submission', created.assignment], created);
    },
  });
}

/**
 * Persist allowlist for mutations: dehydrate a mutation only when it is **paused**
 * (queued offline) and belongs to the `submission` family. Never persist auth or
 * any other token-bearing mutation. Paired with the MSO-4 reads allowlist in
 * `persist.ts` (`shouldDehydrateQuery`).
 */
export const shouldDehydrateSubmissionMutation = (mutation: Mutation): boolean => {
  if (mutation.state.isPaused !== true) return false;
  const key = mutation.options.mutationKey;
  return Array.isArray(key) && key[0] === 'submission';
};
