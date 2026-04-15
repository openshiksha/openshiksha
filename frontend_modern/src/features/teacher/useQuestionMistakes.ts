import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface QuestionMistake {
  id: number;
  question_id: number;
  question_text: string;
  question_type: string;
  regression: number;
  updated_at: string;
}

const fetchQuestionMistakes = async (subjectRoomId: number): Promise<QuestionMistake[]> => {
  const { data } = await apiClient.get<PaginatedResponse<QuestionMistake>>(
    `/question-mistakes/?subject_room=${subjectRoomId}`
  );
  return data.results;
};

export const useQuestionMistakes = (subjectRoomId: number | undefined) =>
  useQuery<QuestionMistake[]>({
    queryKey: ['question-mistakes', subjectRoomId],
    queryFn: () => fetchQuestionMistakes(subjectRoomId!),
    enabled: !!subjectRoomId,
    staleTime: 2 * 60 * 1000,
  });
