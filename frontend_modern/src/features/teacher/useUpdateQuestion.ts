import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { QuestionCreate } from '@/types/index';

interface UpdateQuestionResponse {
  id: number;
}

const updateQuestion = async ({
  id,
  data,
}: {
  id: number;
  data: QuestionCreate;
}): Promise<UpdateQuestionResponse> => {
  const response = await apiClient.patch<UpdateQuestionResponse>(`/questions/${id}/`, data);
  return response.data;
};

export const useUpdateQuestion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: updateQuestion,
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      queryClient.invalidateQueries({ queryKey: ['question', id] });
    },
  });
};
