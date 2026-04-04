import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Assignment, Submission } from '@/types/index';

export interface SubmissionWithStudent extends Submission {
  student_name: string;
}

export interface TeacherAssignmentDetail extends Assignment {
  submissions: SubmissionWithStudent[];
}

const fetchAssignmentMeta = async (id: number): Promise<Assignment> => {
  const response = await apiClient.get<Assignment>(`/assignments/${id}/`);
  return response.data;
};

const fetchAssignmentSubmissions = async (id: number): Promise<SubmissionWithStudent[]> => {
  const response = await apiClient.get<SubmissionWithStudent[]>(`/assignments/${id}/submissions/`);
  return response.data;
};

export const useTeacherAssignmentDetail = (id: number) => {
  const metaQuery = useQuery<Assignment>({
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
