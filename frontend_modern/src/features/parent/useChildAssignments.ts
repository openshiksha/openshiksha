import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Assignment } from '@/types/index';

const fetchChildAssignments = async (childId: number): Promise<Assignment[]> => {
  const { data } = await apiClient.get<{ results: Assignment[] } | Assignment[]>(
    `/assignments/?student=${childId}`,
  );
  return Array.isArray(data) ? data : (data as { results: Assignment[] }).results ?? [];
};

export const useChildAssignments = (childId: number | undefined) =>
  useQuery<Assignment[]>({
    queryKey: ['parent', 'assignments', childId],
    queryFn: () => fetchChildAssignments(childId!),
    enabled: !!childId,
    staleTime: 2 * 60 * 1000,
  });
