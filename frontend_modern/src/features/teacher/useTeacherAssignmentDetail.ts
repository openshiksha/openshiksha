import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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

const patchAssignmentDueAt = async (id: number, dueAt: string): Promise<Assignment> => {
  const response = await apiClient.patch<Assignment>(`/assignments/${id}/`, { due_at: dueAt });
  return response.data;
};

const closeAssignment = async (id: number): Promise<Assignment> => {
  const response = await apiClient.post<Assignment>(`/assignments/${id}/close/`);
  return response.data;
};

const reopenAssignment = async (id: number): Promise<Assignment> => {
  const response = await apiClient.post<Assignment>(`/assignments/${id}/reopen/`);
  return response.data;
};

export const useTeacherAssignmentDetail = (id: number) => {
  const queryClient = useQueryClient();

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

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['teacher-assignment', id] });
    queryClient.invalidateQueries({ queryKey: ['teacher-assignments'] });
  };

  const updateDueAtMutation = useMutation({
    mutationFn: (dueAt: string) => patchAssignmentDueAt(id, dueAt),
    onSuccess: invalidate,
  });

  const closeMutation = useMutation({
    mutationFn: () => closeAssignment(id),
    onSuccess: invalidate,
  });

  const reopenMutation = useMutation({
    mutationFn: () => reopenAssignment(id),
    onSuccess: invalidate,
  });

  return { metaQuery, submissionsQuery, updateDueAtMutation, closeMutation, reopenMutation };
};
