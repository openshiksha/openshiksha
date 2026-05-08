import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Question, PaginatedResponse } from '@/types/index';

interface QuestionListFilters {
  subject?: number;
  chapter?: number;
  standard?: number;
  search?: string;
  difficulty?: number;
}

const fetchQuestions = async (filters: QuestionListFilters): Promise<Question[]> => {
  const params = new URLSearchParams();
  if (filters.subject) params.set('subject', String(filters.subject));
  if (filters.chapter) params.set('chapter', String(filters.chapter));
  if (filters.standard) params.set('standard', String(filters.standard));
  if (filters.search) params.set('search', filters.search);
  if (filters.difficulty) params.set('difficulty', String(filters.difficulty));

  const response = await apiClient.get<PaginatedResponse<Question>>(
    `/questions/?${params.toString()}`
  );
  return response.data.results;
};

export const useQuestionList = (filters: QuestionListFilters = {}) => {
  return useQuery<Question[]>({
    queryKey: ['questions', filters],
    queryFn: () => fetchQuestions(filters),
    staleTime: 2 * 60 * 1000,
  });
};
