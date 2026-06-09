import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { AssignmentDetail, Submission } from '@/types/index';

export interface SubmissionWithStudent extends Submission {
  student_name: string;
}

export interface TeacherAssignmentDetail extends AssignmentDetail {
  submissions: SubmissionWithStudent[];
}

const fetchAssignmentMeta = async (id: number): Promise<AssignmentDetail> => {
  // The retrieve endpoint serves AssignmentDetailSerializer — it embeds the
  // snapshot-rendered problem-set + questions (AIV-2b) and ``snapshot_drift``
  // (AIV-5). The list endpoint uses AssignmentSerializer (no questions); only
  // the detail view carries this richer shape.
  const response = await apiClient.get<AssignmentDetail>(`/assignments/${id}/`);
  return response.data;
};

const fetchAssignmentSubmissions = async (id: number): Promise<SubmissionWithStudent[]> => {
  const response = await apiClient.get<SubmissionWithStudent[]>(`/assignments/${id}/submissions/`);
  return response.data;
};

export const useTeacherAssignmentDetail = (id: number) => {
  const metaQuery = useQuery<AssignmentDetail>({
    queryKey: ['teacher-assignment', id],
    queryFn: () => fetchAssignmentMeta(id),
    staleTime: 60 * 1000,
    enabled: !!id,
  });

  const submissionsQuery = useQuery<SubmissionWithStudent[]>({
    queryKey: ['teacher-assignment-submissions', id],
    queryFn: () => fetchAssignmentSubmissions(id),
    staleTime: 60 * 1000,
    enabled: !!id,
  });

  return { metaQuery, submissionsQuery };
};
