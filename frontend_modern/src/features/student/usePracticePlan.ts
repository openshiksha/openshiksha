import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { ContentRecommendation } from './useRecommendations';

export interface PracticePlan {
  id: number;
  subject_room: number;
  plan_date: string;
  estimated_minutes: number;
  is_completed: boolean;
  recommendations: ContentRecommendation[];
  generated_at: string;
}

const fetchTodaysPlan = async (): Promise<PracticePlan | null> => {
  try {
    const response = await apiClient.get<PracticePlan>('/ai/practice-plans/today/');
    // 204 No Content = no plan for today yet (the empty state).
    if (response.status === 204 || !response.data) return null;
    return response.data;
  } catch (err: unknown) {
    // Tolerate the legacy 404 empty-state response during the rollout window.
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr.response?.status === 404) return null;
    }
    throw err;
  }
};

export const usePracticePlan = () => {
  return useQuery<PracticePlan | null>({
    queryKey: ['ai', 'practice-plan', 'today'],
    queryFn: fetchTodaysPlan,
    staleTime: 5 * 60 * 1000,
  });
};
