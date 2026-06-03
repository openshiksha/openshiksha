import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface Classroom {
  id: number;
  school: number;
  standard: number;
  standard_number: number;
  division: string;
  class_teacher: number | null;
  class_teacher_name: string | null;
  academic_year: string;
  is_active: boolean;
  student_count: number;
  created_at: string;
}

export interface ClassroomWriteInput {
  standard: number;
  division: string;
  class_teacher?: number | null;
  academic_year: string;
}

export interface EnrollmentResult {
  enrolled?: number[];
  unenrolled?: number[];
  invalid_ids: number[];
  student_count: number;
}

const fetchClassrooms = async (includeInactive: boolean): Promise<Classroom[]> => {
  const response = await apiClient.get<PaginatedResponse<Classroom>>('/classrooms/', {
    params: includeInactive ? { include_inactive: 'true' } : undefined,
  });
  return response.data.results;
};

const fetchClassroom = async (id: number): Promise<Classroom> => {
  const response = await apiClient.get<Classroom>(`/classrooms/${id}/`);
  return response.data;
};

export const useClassrooms = (includeInactive = false) =>
  useQuery<Classroom[]>({
    queryKey: ['admin', 'classrooms', { includeInactive }],
    queryFn: () => fetchClassrooms(includeInactive),
    staleTime: 60 * 1000,
  });

export const useClassroom = (id: number) =>
  useQuery<Classroom>({
    queryKey: ['admin', 'classroom', id],
    queryFn: () => fetchClassroom(id),
    staleTime: 60 * 1000,
  });

export const useCreateClassroom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ClassroomWriteInput) => {
      const response = await apiClient.post<Classroom>('/classrooms/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classrooms'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'summary'] });
    },
  });
};

export const useUpdateClassroom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<ClassroomWriteInput> }) => {
      const response = await apiClient.patch<Classroom>(`/classrooms/${id}/`, data);
      return response.data;
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classrooms'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'classroom', updated.id] });
    },
  });
};

export const useDeleteClassroom = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/classrooms/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classrooms'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'summary'] });
    },
  });
};

export const useClassroomEnrollment = () => {
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
      const response = await apiClient.post<EnrollmentResult>(`/classrooms/${id}/${action}/`, {
        student_ids: studentIds,
      });
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'classroom', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'classrooms'] });
    },
  });
};
