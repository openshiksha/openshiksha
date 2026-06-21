import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface RemoveQuestionPayload {
  problemSetId: number;
  questionId: number;
}

const removeQuestion = async ({ problemSetId, questionId }: RemoveQuestionPayload) => {
  const response = await apiClient.post(
    `/problem-sets/${problemSetId}/remove-question/`,
    { question_id: questionId },
  );
  return response.data;
};

/**
 * TW-2 / AIV-4: drop a question from the live problem set.
 *
 * Existing assignments using this set are unaffected — they grade and render
 * from their per-assignment ``assigned_content`` snapshot (AIV-1/2). Verified
 * by ``apps/api/tests/test_problemset_edit_safety.py``.
 */
export const useRemoveQuestionFromProblemSet = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: removeQuestion,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['problem-sets'] });
      queryClient.invalidateQueries({
        queryKey: ['problem-set-preview', variables.problemSetId],
      });
    },
  });
};
