import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type MilestoneTier = 'none' | 'starter' | 'week' | 'month' | 'champion';

export interface StreakData {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
  streak_grace_used: boolean;
  milestone_tier: MilestoneTier;
}

export const useStreak = () =>
  useQuery<StreakData>({
    queryKey: ['student', 'streak'],
    queryFn: async () => {
      const { data } = await apiClient.get<StreakData>('/users/me/streak/');
      return data;
    },
    staleTime: 60_000,
  });
