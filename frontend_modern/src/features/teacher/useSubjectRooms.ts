import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface TeacherSubjectRoom {
  id: number;
  classroom: number;
  classroom_display: string;
  subject: number;
  subject_name: string;
  teacher: number;
  teacher_name: string;
  is_active: boolean;
  student_count: number;
}

const fetchSubjectRooms = async (): Promise<TeacherSubjectRoom[]> => {
  const response = await apiClient.get<PaginatedResponse<TeacherSubjectRoom>>(
    '/subject-rooms/'
  );
  return response.data.results;
};

export const useSubjectRooms = () => {
  return useQuery<TeacherSubjectRoom[]>({
    queryKey: ['subject-rooms'],
    queryFn: fetchSubjectRooms,
    staleTime: 5 * 60 * 1000,
  });
};
