import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { BrowseChapter } from '@/types/index';

export const useBrowseChapters = (subjectId?: number | string, standardId?: number | string) => {
  const params: Record<string, string> = {};
  if (subjectId) params.subject = String(subjectId);
  if (standardId) params.standard = String(standardId);

  return useQuery<BrowseChapter[]>({
    queryKey: ['browse-chapters', subjectId, standardId],
    queryFn: async () => {
      const res = await apiClient.get<BrowseChapter[]>('/questions/browse/', { params });
      return res.data;
    },
  });
};
