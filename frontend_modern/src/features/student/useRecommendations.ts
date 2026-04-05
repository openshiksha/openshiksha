import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface ContentRecommendation {
  id: number;
  chapter: number;
  chapter_name: string;
  subject_name: string;
  subject_room: number;
  problem_set: number | null;
  reason: string;
  reason_display: string;
  priority: 1 | 2 | 3 | 4; // 1=urgent, 2=high, 3=medium, 4=low
  priority_display: string;
  score_snapshot: number;
  is_actioned: boolean;
  is_active: boolean;
  generated_at: string;
  actioned_at: string | null;
}

const fetchRecommendations = async (): Promise<ContentRecommendation[]> => {
  const response = await apiClient.get<PaginatedResponse<ContentRecommendation>>(
    '/ai/recommendations/?is_active=true'
  );
  return response.data.results;
};

export const useRecommendations = () => {
  return useQuery<ContentRecommendation[]>({
    queryKey: ['ai', 'recommendations'],
    queryFn: fetchRecommendations,
    staleTime: 2 * 60 * 1000,
  });
};
