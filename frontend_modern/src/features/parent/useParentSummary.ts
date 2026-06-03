import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface ParentAlert {
  severity: 'info' | 'attention' | 'urgent';
  label: string;
  detail: string;
}

export interface HomeActivity {
  title: string;
  description: string;
  chapter_name?: string;
}

export interface WeakStrongChapter {
  chapter_id: number;
  chapter_name: string;
  avg_score: number;
  tick_count: number;
}

export interface ParentProgressSummary {
  id: number;
  parent: number;
  child: number;
  child_username: string;
  child_name: string;
  week_start: string;
  week_end: string;
  summary_text: string;
  language: 'en' | 'hi';
  ticks_recorded: number;
  active_days: number;
  avg_score: number;
  score_delta: number;
  weak_chapters: WeakStrongChapter[];
  strong_chapters: WeakStrongChapter[];
  home_activities: HomeActivity[];
  alerts: ParentAlert[];
  has_urgent_alert: boolean;
  model_used: string;
  generated_at: string;
}

export const useLatestParentSummary = (childId: number | undefined) =>
  useQuery<ParentProgressSummary | null>({
    queryKey: ['parent', 'summary', 'latest', childId],
    queryFn: async () => {
      try {
        const { data } = await apiClient.get<ParentProgressSummary>(
          `/ai/parent-summaries/latest/?child=${childId}`,
        );
        return data;
      } catch (err: unknown) {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 404) return null;
        throw err;
      }
    },
    enabled: Number.isFinite(childId),
    staleTime: 60 * 1000,
  });

interface GenerateParams {
  child_id: number;
  language?: 'en' | 'hi';
}

export const useGenerateParentSummary = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: GenerateParams) => {
      const { data } = await apiClient.post('/ai/parent-summaries/generate/', payload);
      return data;
    },
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({
        queryKey: ['parent', 'summary', 'latest', vars.child_id],
      });
    },
  });
};
