import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface SRSEntry {
  id: number;
  knowledge_node: number;
  chapter_name: string;
  interval_days: number;
  easiness_factor: number;
  repetitions: number;
  next_review_date: string;
  last_reviewed_at: string | null;
}

const fetchDueEntries = async (): Promise<SRSEntry[]> => {
  const { data } = await apiClient.get<SRSEntry[] | { results: SRSEntry[] }>(
    '/ai/spaced-repetition/due/'
  );
  return Array.isArray(data) ? data : data.results ?? [];
};

export const useSpacedRepetitionDue = () =>
  useQuery<SRSEntry[]>({
    queryKey: ['srs', 'due'],
    queryFn: fetchDueEntries,
    staleTime: 10 * 60 * 1000,
  });
