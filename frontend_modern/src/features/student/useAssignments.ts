import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Assignment, PaginatedResponse } from '@/types/index';

const fetchAssignments = async (): Promise<Assignment[]> => {
  const response = await apiClient.get<PaginatedResponse<Assignment>>('/assignments/');
  return response.data.results;
};

export const useAssignments = () => {
  return useQuery<Assignment[]>({
    queryKey: ['assignments'],
    queryFn: fetchAssignments,
    staleTime: 30 * 1000, // 30 seconds
  });
};
