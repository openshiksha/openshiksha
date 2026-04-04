import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { QuestionCreate } from '@/types/index';

interface CreateQuestionResponse {
  id: number;
  created_at: string;
}

const createQuestion = async (data: QuestionCreate): Promise<CreateQuestionResponse> => {
  const response = await apiClient.post<CreateQuestionResponse>('/questions/', data);
  return response.data;
};

export const useCreateQuestion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createQuestion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
    },
  });
};
