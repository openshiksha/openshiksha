import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Question } from '@/types/index';

export interface SRSDrillData {
  entry_id: number;
  chapter_name: string;
  subject_name: string;
  questions: Question[];
}

export interface SRSReviewResult {
  id: number;
  knowledge_node: number;
  chapter_name: string;
  interval_days: number;
  easiness_factor: number;
  repetitions: number;
  next_review_date: string;
  last_reviewed_at: string | null;
  score: number;
}

export const useSRSDrill = (entryId: number | null) =>
  useQuery<SRSDrillData>({
    queryKey: ['srs', 'drill', entryId],
    queryFn: async () => {
      const { data } = await apiClient.get<SRSDrillData>(
        `/ai/spaced-repetition/${entryId}/review/`
      );
      return data;
    },
    enabled: entryId != null && !Number.isNaN(entryId),
    staleTime: 0,
  });

export const useMarkReviewed = () => {
  const queryClient = useQueryClient();
  return useMutation<
    SRSReviewResult,
    Error,
    { entryId: number; answers: Record<string, string> }
  >({
    mutationFn: async ({ entryId, answers }) => {
      const { data } = await apiClient.post<SRSReviewResult>(
        `/ai/spaced-repetition/${entryId}/mark-reviewed/`,
        { answers }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['srs', 'due'] });
      queryClient.invalidateQueries({ queryKey: ['srs', 'drill'] });
    },
  });
};
