import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type CalibrationFlag =
  | 'ok'
  | 'mislabeled'
  | 'too_easy'
  | 'too_hard'
  | 'low_discrimination';

export interface DifficultyCalibration {
  id: number;
  subject_room: number;
  subject_name: string;
  question_subpart: number;
  question_id: number;
  subpart_index: number;
  chapter_name: string;
  question_preview: string;
  sample_size: number;
  attempt_count: number;
  facility_index: number;
  discrimination_index: number | null;
  empirical_difficulty: number;
  declared_difficulty: number;
  difficulty_delta: number;
  flag: CalibrationFlag;
  flag_display: string;
  needs_review: boolean;
  computed_at: string;
}

export interface CalibrationSummary {
  subject_room: number;
  total_calibrated: number;
  flagged: number;
  by_flag: Record<CalibrationFlag, number>;
}

interface PaginatedResponse<T> {
  results: T[];
}

const fetchFlaggedCalibrations = async (
  subjectRoomId: number
): Promise<DifficultyCalibration[]> => {
  const response = await apiClient.get<PaginatedResponse<DifficultyCalibration>>(
    `/ai/difficulty-calibrations/?subject_room=${subjectRoomId}&needs_review=true`
  );
  return response.data.results;
};

const fetchSummary = async (subjectRoomId: number): Promise<CalibrationSummary> => {
  const response = await apiClient.get<CalibrationSummary>(
    `/ai/difficulty-calibrations/summary/?subject_room=${subjectRoomId}`
  );
  return response.data;
};

export const useFlaggedCalibrations = (subjectRoomId: number, enabled: boolean) =>
  useQuery<DifficultyCalibration[]>({
    queryKey: ['ai', 'difficulty-calibrations', subjectRoomId],
    queryFn: () => fetchFlaggedCalibrations(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

export const useCalibrationSummary = (subjectRoomId: number, enabled: boolean) =>
  useQuery<CalibrationSummary>({
    queryKey: ['ai', 'difficulty-calibrations', 'summary', subjectRoomId],
    queryFn: () => fetchSummary(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

export const useRefreshCalibrations = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/ai/difficulty-calibrations/refresh/', {
        subject_room_id: subjectRoomId,
      });
    },
    onSuccess: () => {
      // Recompute is async on the server; refetch shortly after to pick up new rows.
      setTimeout(() => {
        queryClient.invalidateQueries({
          queryKey: ['ai', 'difficulty-calibrations', subjectRoomId],
        });
        queryClient.invalidateQueries({
          queryKey: ['ai', 'difficulty-calibrations', 'summary', subjectRoomId],
        });
      }, 2500);
    },
  });
};
