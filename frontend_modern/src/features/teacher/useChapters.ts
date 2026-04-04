import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { ChapterItem, PaginatedResponse } from '@/types/index';

const fetchChapters = async (subjectId?: number, standardId?: number): Promise<ChapterItem[]> => {
  const params: Record<string, string> = {};
  if (subjectId) params.subject = String(subjectId);
  if (standardId) params.standard = String(standardId);
  const response = await apiClient.get<PaginatedResponse<ChapterItem>>('/chapters/', { params });
  return response.data.results;
};

export const useChapters = (subjectId?: number, standardId?: number) => {
  return useQuery<ChapterItem[]>({
    queryKey: ['chapters', subjectId, standardId],
    queryFn: () => fetchChapters(subjectId, standardId),
    enabled: !!subjectId,
    staleTime: 10 * 60 * 1000,
  });
};
