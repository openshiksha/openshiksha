import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';
import type { EnrollmentResult } from './useClassrooms';

export interface AdminSubjectRoom {
  id: number;
  classroom: number;
  classroom_display: string;
  subject: number;
  subject_name: string;
  teacher: number;
  teacher_name: string;
  is_active: boolean;
  student_count: number;
  created_at: string;
}

export interface SubjectRoomWriteInput {
  classroom: number;
  subject: number;
  teacher: number;
}

const fetchSubjectRooms = async (): Promise<AdminSubjectRoom[]> => {
  const response = await apiClient.get<PaginatedResponse<AdminSubjectRoom>>('/subject-rooms/');
  return response.data.results;
};

export const useAdminSubjectRooms = () =>
  useQuery<AdminSubjectRoom[]>({
    queryKey: ['admin', 'subject-rooms'],
    queryFn: fetchSubjectRooms,
    staleTime: 60 * 1000,
  });

export const useCreateSubjectRoom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SubjectRoomWriteInput) => {
      const response = await apiClient.post<AdminSubjectRoom>('/subject-rooms/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'subject-rooms'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'summary'] });
    },
  });
};

export const useSubjectRoomEnrollment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      studentIds,
      action,
    }: {
      id: number;
      studentIds: number[];
      action: 'enroll' | 'unenroll';
    }) => {
      const response = await apiClient.post<EnrollmentResult>(`/subject-rooms/${id}/${action}/`, {
        student_ids: studentIds,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'subject-rooms'] });
    },
  });
};
