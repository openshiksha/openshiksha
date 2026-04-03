import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { AssignmentDetail } from '@/types/index';

const fetchAssignmentDetail = async (id: number): Promise<AssignmentDetail> => {
  const response = await apiClient.get<AssignmentDetail>(`/assignments/${id}/`);
  return response.data;
};

export const useAssignmentDetail = (id: number) => {
  return useQuery<AssignmentDetail>({
    queryKey: ['assignment', id],
    queryFn: () => fetchAssignmentDetail(id),
    staleTime: 60 * 1000, // 1 minute
    enabled: !!id,
  });
};
