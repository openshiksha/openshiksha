import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface AddQuestionPayload {
  problemSetId: number;
  questionId: number;
}

const addQuestion = async ({ problemSetId, questionId }: AddQuestionPayload) => {
  const response = await apiClient.post(
    `/problem-sets/${problemSetId}/add-question/`,
    { question_id: questionId }
  );
  return response.data;
};

export const useAddQuestionToProblemSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addQuestion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['problem-sets'] });
    },
  });
};
