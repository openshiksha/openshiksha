import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface CreateProblemSetInput {
  title: string;
  description?: string;
  standard: number;
  subject: number;
  chapter: number;
  estimated_minutes?: number | null;
  question_ids: number[];
}

interface ProblemSetCreated {
  id: number;
  title: string;
  created_at: string;
}

const createProblemSet = async (data: CreateProblemSetInput): Promise<ProblemSetCreated> => {
  const response = await apiClient.post<ProblemSetCreated>('/problem-sets/', data);
  return response.data;
};

export const useCreateProblemSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProblemSet,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['problem-sets'] });
    },
  });
};
