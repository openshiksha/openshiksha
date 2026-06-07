import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { GenerateQuestionsRequest, GeneratedQuestionDraft } from '@/types/index';

interface GenerateQuestionsResponse {
  questions: GeneratedQuestionDraft[];
  /**
   * False when the backend's LLM cascade was exhausted and it fell back to the
   * deterministic fallback. In that case `questions` is empty and the UI should
   * show an "AI unavailable" message rather than rendering placeholder drafts.
   */
  ai_available: boolean;
}

const generateQuestions = async (
  data: GenerateQuestionsRequest
): Promise<GenerateQuestionsResponse> => {
  const response = await apiClient.post<GenerateQuestionsResponse>(
    '/ai/generate-questions/',
    data
  );
  return response.data;
};

export const useGenerateQuestions = () =>
  useMutation<GenerateQuestionsResponse, Error, GenerateQuestionsRequest>({
    mutationFn: generateQuestions,
  });
