import { useMutationState } from '@tanstack/react-query';

/**
 * MSO-8 — derive the student-facing sync state from the MSO-7 offline submission
 * mutation queue. Kept separate from the SyncStatus components so the module
 * exports only hooks (react-refresh friendliness).
 */

export type SyncState = 'idle' | 'queued' | 'syncing' | 'error';

/** Derive a single sync state from all in-flight/queued `submission` mutations. */
export const useSyncState = (): SyncState => {
  const states = useMutationState({
    filters: { mutationKey: ['submission'] },
    select: (mutation) => ({
      status: mutation.state.status,
      isPaused: mutation.state.isPaused,
    }),
  });

  const hasPaused = states.some((s) => s.isPaused);
  const hasPending = states.some((s) => s.status === 'pending' && !s.isPaused);
  const hasError = states.some((s) => s.status === 'error');

  // Priority: a queued (paused, offline) write is the most important thing to
  // surface; then an active replay; then a settled failure.
  if (hasPaused) return 'queued';
  if (hasPending) return 'syncing';
  if (hasError) return 'error';
  return 'idle';
};

/** Number of submission writes currently queued on the device (paused). */
export const usePendingSyncCount = (): number =>
  useMutationState({
    filters: { mutationKey: ['submission'] },
    select: (mutation) => mutation.state.isPaused,
  }).filter(Boolean).length;
