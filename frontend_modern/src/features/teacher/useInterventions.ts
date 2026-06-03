import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type InterventionStatus = 'open' | 'acknowledged' | 'dismissed' | 'resolved';
export type GapSeverity = 'mild' | 'moderate' | 'severe';

export interface InterventionFocusChapter {
  chapter_id: number;
  chapter_name: string;
  avg_score: number;
  severity: GapSeverity;
}

export interface InterventionMisconception {
  label: string;
  count: number;
}

export interface InterventionSuggestion {
  id: number;
  subject_room: number;
  subject_name: string;
  classroom_label: string;
  student: number;
  student_name: string;
  student_username: string;
  status: InterventionStatus;
  priority: number;
  severity: GapSeverity;
  strategy_text: string;
  avg_score: number;
  gap_count: number;
  focus_chapters: InterventionFocusChapter[];
  misconception_labels: InterventionMisconception[];
  acknowledged_by: number | null;
  acknowledged_at: string | null;
  model_used: string;
  generated_at: string;
}

interface PaginatedResponse<T> {
  results: T[];
}

const fetchInterventions = async (subjectRoomId: number): Promise<InterventionSuggestion[]> => {
  const response = await apiClient.get<PaginatedResponse<InterventionSuggestion>>(
    `/ai/interventions/?subject_room=${subjectRoomId}`
  );
  return response.data.results;
};

export const useInterventions = (subjectRoomId: number, enabled: boolean) =>
  useQuery<InterventionSuggestion[]>({
    queryKey: ['ai', 'interventions', subjectRoomId],
    queryFn: () => fetchInterventions(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

export const useGenerateInterventions = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/ai/interventions/generate/', { subject_room_id: subjectRoomId });
    },
    onSuccess: () => {
      // Generation is async on the server; refetch shortly after to pick up new rows.
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['ai', 'interventions', subjectRoomId] });
      }, 2500);
    },
  });
};

export const useSetInterventionStatus = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      status,
    }: {
      id: number;
      status: 'acknowledged' | 'dismissed' | 'resolved';
    }) => {
      await apiClient.post(`/ai/interventions/${id}/set-status/`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai', 'interventions', subjectRoomId] });
    },
  });
};
