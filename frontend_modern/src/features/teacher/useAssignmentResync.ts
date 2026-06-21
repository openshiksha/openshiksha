import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

/**
 * AIV-6: blast-radius preview returned by ``GET /assignments/<id>/resync-preview/``.
 *
 * Shape matches ``AssignmentViewSet.resync_preview`` — the diff fields are the
 * structured output of ``apps.core.snapshots.diff_snapshots``.
 */
export interface ResyncDiff {
  questions_added: number[];
  questions_removed: number[];
  answer_changes: Array<{
    subpart_id: number;
    question_id: number;
    before: unknown;
    after: unknown;
  }>;
  content_changes: Array<{ subpart_id: number; question_id: number }>;
}

export interface ResyncPreview {
  assignment_id: number;
  has_drift: boolean;
  diff: ResyncDiff;
  affected: {
    submitted_count: number;
    graded_count: number;
    regrade_on_apply: number;
  };
}

const fetchPreview = async (assignmentId: number): Promise<ResyncPreview> => {
  const res = await apiClient.get<ResyncPreview>(
    `/assignments/${assignmentId}/resync-preview/`,
  );
  return res.data;
};

/**
 * Loads the blast-radius preview for a re-sync. ``enabled`` lets the caller
 * defer the network call until the user opens the resync modal — the drift
 * banner itself decides whether to offer the action.
 */
export const useResyncPreview = (assignmentId: number, enabled: boolean) => {
  return useQuery<ResyncPreview>({
    queryKey: ['resync-preview', assignmentId],
    queryFn: () => fetchPreview(assignmentId),
    enabled: !!assignmentId && enabled,
    staleTime: 0,
  });
};

const applyResync = async (assignmentId: number) => {
  const res = await apiClient.post(`/assignments/${assignmentId}/resync/`);
  return res.data;
};

export const useApplyResync = (assignmentId: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => applyResync(assignmentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['teacher-assignment', assignmentId] });
      qc.invalidateQueries({ queryKey: ['teacher-assignment-submissions', assignmentId] });
      qc.invalidateQueries({ queryKey: ['resync-preview', assignmentId] });
    },
  });
};

const undoResync = async (assignmentId: number) => {
  const res = await apiClient.post(`/assignments/${assignmentId}/undo-resync/`);
  return res.data;
};

export const useUndoResync = (assignmentId: number) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => undoResync(assignmentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['teacher-assignment', assignmentId] });
      qc.invalidateQueries({ queryKey: ['resync-preview', assignmentId] });
    },
  });
};
