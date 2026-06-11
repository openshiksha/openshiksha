import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type OpenGradeStatus = 'pending' | 'ai_graded' | 'reviewed' | 'failed';

export interface CriterionScore {
  label: string;
  awarded: number;
  max: number;
  comment: string;
}

/** Mirrors OpenResponseGradeSerializer (backend/openshiksha/apps/ai/serializers.py). */
export interface OpenResponseGrade {
  id: number;
  subpart: number;
  question_text: string;
  student: number;
  student_name: string;
  student_username: string;
  subject_room: number;
  subject_name: string;
  assignment: number | null;
  response_text: string;
  status: OpenGradeStatus;
  max_marks: number;
  suggested_score: number | null;
  feedback: string;
  criterion_scores: CriterionScore[];
  confidence: number | null;
  final_score: number | null;
  teacher_comment: string;
  reviewed_by: number | null;
  reviewed_at: string | null;
  effective_score: number | null;
  is_reviewed: boolean;
  model_used: string;
  error_detail: string;
  created_at: string;
  updated_at: string;
}

export interface OpenGradeFilters {
  subjectRoomId?: number;
  status?: OpenGradeStatus;
}

const gradesKey = (filters: OpenGradeFilters) => [
  'ai',
  'open-grades',
  filters.subjectRoomId ?? 'all',
  filters.status ?? 'all',
];

/**
 * AI grading runs async (submit returns 202 with a pending row; a Celery task
 * fills in the suggestion). While any visible row is pending the list
 * refetches on an interval so cards flip to ai_graded/failed by themselves —
 * and polling stops as soon as nothing is pending.
 */
export const useOpenGrades = (filters: OpenGradeFilters, enabled = true, pollIntervalMs = 3000) =>
  useQuery<OpenResponseGrade[]>({
    queryKey: gradesKey(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.subjectRoomId != null) params.set('subject_room', String(filters.subjectRoomId));
      if (filters.status) params.set('status', filters.status);
      const qs = params.toString();
      const { data } = await apiClient.get<OpenResponseGrade[] | { results: OpenResponseGrade[] }>(
        `/ai/open-grades/${qs ? `?${qs}` : ''}`
      );
      return Array.isArray(data) ? data : (data.results ?? []);
    },
    enabled,
    staleTime: 30 * 1000,
    refetchInterval: (query) =>
      (query.state.data ?? []).some((g) => g.status === 'pending') ? pollIntervalMs : false,
  });

/** Invalidate every open-grades list (all filter combinations). */
const invalidateGrades = (queryClient: ReturnType<typeof useQueryClient>) =>
  queryClient.invalidateQueries({ queryKey: ['ai', 'open-grades'] });

export const useReviewOpenGrade = () => {
  const queryClient = useQueryClient();
  return useMutation<
    OpenResponseGrade,
    Error,
    { id: number; final_score: number; teacher_comment?: string }
  >({
    mutationFn: async ({ id, final_score, teacher_comment }) => {
      const { data } = await apiClient.post<OpenResponseGrade>(`/ai/open-grades/${id}/review/`, {
        final_score,
        ...(teacher_comment ? { teacher_comment } : {}),
      });
      return data;
    },
    onSuccess: () => invalidateGrades(queryClient),
  });
};

export const useRegradeOpenGrade = () => {
  const queryClient = useQueryClient();
  return useMutation<OpenResponseGrade, Error, { id: number }>({
    mutationFn: async ({ id }) => {
      const { data } = await apiClient.post<OpenResponseGrade>(
        `/ai/open-grades/${id}/regrade/`,
        {}
      );
      return data;
    },
    onSuccess: () => invalidateGrades(queryClient),
  });
};

/** Extract the server's `detail` message from an axios-shaped error (e.g. a 400/409). */
export const gradeErrorDetail = (error: unknown): string | null => {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail ===
      'string'
  ) {
    return (error as { response: { data: { detail: string } } }).response.data.detail;
  }
  return null;
};
