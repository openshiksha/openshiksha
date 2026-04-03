import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Assignment } from '@/types/index';

interface CreateAssignmentInput {
  subject_room: number;
  problem_set_id: number;
  due_at: string;
}

const createAssignment = async (data: CreateAssignmentInput): Promise<Assignment> => {
  const response = await apiClient.post<Assignment>('/assignments/', data);
  return response.data;
};

export const useCreateAssignment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
    },
  });
};
