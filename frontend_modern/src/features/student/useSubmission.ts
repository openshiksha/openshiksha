import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Submission, PaginatedResponse } from '@/types/index';
import {
  SUBMISSION_CREATE_KEY,
  SUBMISSION_PATCH_KEY,
  type PatchSubmissionVars,
} from '@/shared/query/offlineMutations';

const fetchSubmission = async (assignmentId: number): Promise<Submission | null> => {
  const response = await apiClient.get<PaginatedResponse<Submission>>(
    `/submissions/?assignment=${assignmentId}`
  );
  return response.data.results[0] ?? null;
};

export const useSubmission = (assignmentId: number) => {
  return useQuery<Submission | null>({
    queryKey: ['submission', assignmentId],
    queryFn: () => fetchSubmission(assignmentId),
    staleTime: 30 * 1000,
    enabled: !!assignmentId,
  });
};

/**
 * MSO-7: submission writes are keyed mutations whose `mutationFn`, `networkMode:
 * 'offlineFirst'`, and cache-reconciling `onSuccess` are registered once in
 * `offlineMutations.ts`. The components reference them only by `mutationKey`, so
 * offline they pause + persist + replay instead of failing — and a rehydrated
 * paused mutation (no live observer) still resolves its function and updates the
 * cache on replay.
 */
export const useCreateSubmission = () => {
  return useMutation<Submission, Error, number>({
    mutationKey: SUBMISSION_CREATE_KEY,
  });
};

// `assignmentId` is no longer needed for cache reconciliation (the default
// `onSuccess` derives it from the server response) but the signature is kept so
// callers don't change.
export const usePatchSubmission = (_assignmentId: number) => {
  return useMutation<Submission, Error, PatchSubmissionVars>({
    mutationKey: SUBMISSION_PATCH_KEY,
  });
};
