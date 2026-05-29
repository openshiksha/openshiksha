import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface AdminSchoolSummary {
  school: { id: number; name: string };
  classroom_count: number;
  teacher_count: number;
  student_count: number;
  active_subject_rooms: number;
}

const fetchSummary = async (): Promise<AdminSchoolSummary> => {
  const response = await apiClient.get<AdminSchoolSummary>('/classrooms/summary/');
  return response.data;
};

export const useAdminSummary = () => {
  return useQuery<AdminSchoolSummary>({
    queryKey: ['admin', 'summary'],
    queryFn: fetchSummary,
    staleTime: 60 * 1000,
  });
};
