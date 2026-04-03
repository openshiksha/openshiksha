import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Assignment, PaginatedResponse } from '@/types/index';

const fetchTeacherAssignments = async (): Promise<Assignment[]> => {
  const response = await apiClient.get<PaginatedResponse<Assignment>>('/assignments/');
  return response.data.results;
};

export const useTeacherAssignments = () => {
  return useQuery<Assignment[]>({
    queryKey: ['teacher-assignments'],
    queryFn: fetchTeacherAssignments,
    staleTime: 2 * 60 * 1000,
  });
};
