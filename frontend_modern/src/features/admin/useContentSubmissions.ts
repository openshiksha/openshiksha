import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

/**
 * Hooks over the admin-only content-submission review API (CP-3, PR #518).
 *
 * The endpoints are read-only plus three transition actions; every state
 * change goes through the backend's `transition_to()` state machine, so the
 * UI never decides legality — an illegal move comes back as a 409 and is
 * surfaced verbatim. Approving materializes the pack into the shared bank
 * server-side; this client only triggers and re-fetches.
 */

export type SubmissionState = 'pending' | 'approved' | 'rejected' | 'superseded';

export interface PackProvenance {
  author: string;
  license: string;
  source?: string;
  contact?: string;
}

/** One subpart as authored in the pack payload (content_pack.schema.json v1.0). */
export interface PackSubpart {
  index: number;
  subpart_type?: string;
  question_text: string;
  options?: { key: string; text: string }[] | null;
  correct_answer?: Record<string, unknown>;
  variable_constraints?: Record<string, unknown> | null;
  image_url?: string;
  solution_text?: string;
  hint_text?: string;
  widget_kind?: string;
  widget_config?: Record<string, unknown>;
}

/** One question as authored in the pack payload. */
export interface PackQuestion {
  standard: number;
  subject: string;
  chapter: string;
  question_type?: string;
  difficulty?: number;
  stem_text?: string;
  tags?: string[];
  subparts: PackSubpart[];
}

export interface ContentSubmissionSummary {
  id: number;
  name: string;
  pack_hash: string;
  provenance: PackProvenance;
  state: SubmissionState;
  state_display: string;
  note: string;
  reviewer_username: string | null;
  question_count: number;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
}

export interface ContentSubmissionDetail extends ContentSubmissionSummary {
  payload: {
    pack_version: string;
    name?: string;
    provenance: PackProvenance;
    questions: PackQuestion[];
  } | null;
}

interface Paginated<T> {
  count: number;
  results: T[];
}

export const useContentSubmissions = (state: SubmissionState | 'all') => {
  return useQuery<ContentSubmissionSummary[]>({
    queryKey: ['content-submissions', state],
    queryFn: async () => {
      const params = state === 'all' ? {} : { state };
      const response = await apiClient.get<Paginated<ContentSubmissionSummary>>(
        '/content-submissions/',
        { params },
      );
      return response.data.results;
    },
  });
};

export const useContentSubmission = (id: number | null) => {
  return useQuery<ContentSubmissionDetail>({
    queryKey: ['content-submissions', 'detail', id],
    queryFn: async () => {
      const response = await apiClient.get<ContentSubmissionDetail>(`/content-submissions/${id}/`);
      return response.data;
    },
    enabled: id !== null,
  });
};

export type SubmissionAction = 'approve' | 'reject' | 'reopen';

export interface TransitionInput {
  id: number;
  action: SubmissionAction;
  note?: string;
}

export const useSubmissionTransition = () => {
  const queryClient = useQueryClient();
  return useMutation<ContentSubmissionDetail, unknown, TransitionInput>({
    mutationFn: async ({ id, action, note }) => {
      const response = await apiClient.post<ContentSubmissionDetail>(
        `/content-submissions/${id}/${action}/`,
        note ? { note } : {},
      );
      return response.data;
    },
    onSuccess: () => {
      // Both the queue rows and the open detail changed state server-side.
      queryClient.invalidateQueries({ queryKey: ['content-submissions'] });
    },
  });
};
