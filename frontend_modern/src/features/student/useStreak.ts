import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface StreakData {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
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
