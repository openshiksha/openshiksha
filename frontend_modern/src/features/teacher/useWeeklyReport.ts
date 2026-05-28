import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface WeeklyReportChapter {
  chapter_id: number;
  chapter_name: string;
  avg_score: number;
  tick_count: number;
}

export interface WeeklyClassReport {
  id: number;
  subject_room: number;
  subject_name: string;
  classroom_label: string;
  week_start: string;
  week_end: string;
  summary_text: string;
  total_students: number;
  active_students: number;
  participation_rate: number;
  ticks_recorded: number;
  class_avg_score: number;
  struggling_chapters: WeeklyReportChapter[];
  strong_chapters: WeeklyReportChapter[];
  model_used: string;
  generated_at: string;
}

const fetchLatestReport = async (subjectRoomId: number): Promise<WeeklyClassReport | null> => {
  try {
    const response = await apiClient.get<WeeklyClassReport>(
      `/ai/weekly-reports/latest/?subject_room=${subjectRoomId}`
    );
    return response.data;
  } catch (error: unknown) {
    // 404 simply means no report has been generated yet.
    if (
      typeof error === 'object' &&
      error !== null &&
      'response' in error &&
      (error as { response?: { status?: number } }).response?.status === 404
    ) {
      return null;
    }
    throw error;
  }
};

export const useWeeklyReport = (subjectRoomId: number, enabled: boolean) => {
  return useQuery<WeeklyClassReport | null>({
    queryKey: ['ai', 'weekly-report', subjectRoomId],
    queryFn: () => fetchLatestReport(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });
};
