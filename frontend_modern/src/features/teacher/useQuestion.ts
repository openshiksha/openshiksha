import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Question } from '@/types/index';

const fetchQuestion = async (id: number): Promise<Question> => {
  const response = await apiClient.get<Question>(`/questions/${id}/`);
  return response.data;
};

export const useQuestion = (id: number | undefined) =>
  useQuery<Question>({
    queryKey: ['question', id],
    queryFn: () => fetchQuestion(id!),
    enabled: id !== undefined,
    staleTime: 2 * 60 * 1000,
  });
