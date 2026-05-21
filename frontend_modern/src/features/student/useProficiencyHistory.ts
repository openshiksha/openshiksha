import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface ProficiencySnapshot {
  id: number;
  score: number;
  recorded_at: string;
}

interface HistoryParams {
  tagId: number;
  subjectRoomId: number;
  studentId?: number;
}

const fetchHistory = async (params: HistoryParams): Promise<ProficiencySnapshot[]> => {
  const searchParams = new URLSearchParams({
    tag: String(params.tagId),
    subject_room: String(params.subjectRoomId),
  });
  if (params.studentId) searchParams.set('student', String(params.studentId));
  const { data } = await apiClient.get<ProficiencySnapshot[]>(
    `/proficiency/history/?${searchParams}`,
  );
  return Array.isArray(data) ? data : [];
};

export const useProficiencyHistory = (params: HistoryParams | null) =>
  useQuery<ProficiencySnapshot[]>({
    queryKey: ['proficiency', 'history', params],
    queryFn: () => fetchHistory(params!),
    enabled: !!params,
    staleTime: 5 * 60 * 1000,
  });
