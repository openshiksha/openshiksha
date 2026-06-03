import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface ClassInsight {
  id: number;
  chapter: number;
  chapter_name: string;
  insight_type: 'struggling' | 'at_risk' | 'proficient';
  class_avg_score: number;
  students_assessed: number;
  students_struggling: number;
  pct_struggling: number;
  generated_at: string;
}

const fetchClassInsights = async (subjectRoomId: number): Promise<ClassInsight[]> => {
  const response = await apiClient.get<PaginatedResponse<ClassInsight>>(
    `/ai/class-insights/?subject_room=${subjectRoomId}`
  );
  return response.data.results;
};

export const useClassInsights = (subjectRoomId: number, enabled: boolean) => {
  return useQuery<ClassInsight[]>({
    queryKey: ['ai', 'class-insights', subjectRoomId],
    queryFn: () => fetchClassInsights(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });
};
