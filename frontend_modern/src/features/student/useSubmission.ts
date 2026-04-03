import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Submission, PaginatedResponse } from '@/types/index';

const fetchSubmission = async (assignmentId: number): Promise<Submission | null> => {
  const response = await apiClient.get<PaginatedResponse<Submission>>(
    `/submissions/?assignment=${assignmentId}`
  );
  return response.data.results[0] ?? null;
};

const createSubmission = async (assignmentId: number): Promise<Submission> => {
  const response = await apiClient.post<Submission>('/submissions/', {
    assignment: assignmentId,
  });
  return response.data;
};

const patchSubmission = async (
  id: number,
  data: Partial<Pick<Submission, 'answers' | 'completion' | 'submitted_at'>>
): Promise<Submission> => {
  const response = await apiClient.patch<Submission>(`/submissions/${id}/`, data);
  return response.data;
};

export const useSubmission = (assignmentId: number) => {
  return useQuery<Submission | null>({
    queryKey: ['submission', assignmentId],
    queryFn: () => fetchSubmission(assignmentId),
    staleTime: 30 * 1000,
    enabled: !!assignmentId,
  });
};

export const useCreateSubmission = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createSubmission,
    onSuccess: (data) => {
      queryClient.setQueryData(['submission', data.assignment], data);
    },
  });
};

export const usePatchSubmission = (assignmentId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof patchSubmission>[1] }) =>
      patchSubmission(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(['submission', assignmentId], updated);
      // Invalidate assignment list so completion/score reflects in dashboard
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
};
