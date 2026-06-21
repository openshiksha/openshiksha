import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export type AssignmentDraftStatus = 'pending' | 'ready' | 'approved' | 'dismissed' | 'failed';

export interface DraftTargetChapter {
  chapter_id: number;
  chapter_name: string;
  avg_score: number;
  tick_count: number;
}

export interface DraftSelectedQuestion {
  question_id: number;
  chapter_id: number;
  chapter_name: string;
  difficulty: number;
  question_type: string;
  preview: string;
  reason: string;
}

/** Mirrors AssignmentDraftSerializer (backend/openshiksha/apps/ai/serializers.py). */
export interface AssignmentDraft {
  id: number;
  subject_room: number;
  subject_name: string;
  classroom_label: string;
  status: AssignmentDraftStatus;
  title: string;
  rationale_text: string;
  target_difficulty: number;
  requested_size: number;
  target_chapters: DraftTargetChapter[];
  selected_questions: DraftSelectedQuestion[];
  question_count: number;
  estimated_minutes: number;
  is_actionable: boolean;
  approved_problem_set: number | null;
  approved_assignment: number | null;
  model_used: string;
  error_detail: string;
  created_at: string;
  updated_at: string;
}

const draftsKey = (subjectRoomId: number) => ['ai', 'assignment-drafts', subjectRoomId];

/**
 * Draft assembly is async on the server (generate returns 202 with a pending
 * row; a Celery task fills in the selection + rationale). While any draft is
 * pending the list refetches on an interval so the card flips to ready/failed
 * by itself — and the polling stops as soon as nothing is pending.
 */
export const useAssignmentDrafts = (
  subjectRoomId: number,
  enabled: boolean,
  pollIntervalMs = 3000
) =>
  useQuery<AssignmentDraft[]>({
    queryKey: draftsKey(subjectRoomId),
    queryFn: async () => {
      const { data } = await apiClient.get<AssignmentDraft[] | { results: AssignmentDraft[] }>(
        `/ai/assignment-drafts/?subject_room=${subjectRoomId}`
      );
      return Array.isArray(data) ? data : (data.results ?? []);
    },
    enabled,
    staleTime: 60 * 1000,
    refetchInterval: (query) =>
      (query.state.data ?? []).some((d) => d.status === 'pending') ? pollIntervalMs : false,
  });

export const useGenerateAssignmentDraft = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation<AssignmentDraft, Error, { size?: number; target_difficulty?: number }>({
    mutationFn: async (opts) => {
      const { data } = await apiClient.post<AssignmentDraft>('/ai/assignment-drafts/generate/', {
        subject_room_id: subjectRoomId,
        ...opts,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: draftsKey(subjectRoomId) });
    },
  });
};

export const useApproveAssignmentDraft = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation<AssignmentDraft, Error, { id: number; due_at: string; title?: string }>({
    mutationFn: async ({ id, due_at, title }) => {
      const { data } = await apiClient.post<AssignmentDraft>(
        `/ai/assignment-drafts/${id}/approve/`,
        title ? { due_at, title } : { due_at }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: draftsKey(subjectRoomId) });
    },
  });
};

export const useDismissAssignmentDraft = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation<AssignmentDraft, Error, { id: number }>({
    mutationFn: async ({ id }) => {
      const { data } = await apiClient.post<AssignmentDraft>(
        `/ai/assignment-drafts/${id}/dismiss/`,
        {}
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: draftsKey(subjectRoomId) });
    },
  });
};

/** Extract the server's `detail` message from an axios-shaped error (e.g. a 409). */
export const errorDetail = (error: unknown): string | null => {
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
