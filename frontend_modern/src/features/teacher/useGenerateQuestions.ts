import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { GenerateQuestionsRequest, GeneratedQuestionDraft } from '@/types/index';

interface GenerateQuestionsResponse {
  questions: GeneratedQuestionDraft[];
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
