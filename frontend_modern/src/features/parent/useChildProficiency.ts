import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { StudentProficiency, PaginatedResponse } from '@/types/index';

const fetchChildProficiency = async (childId: number): Promise<StudentProficiency[]> => {
  const { data } = await apiClient.get<PaginatedResponse<StudentProficiency>>(
    `/proficiency/?student=${childId}`
  );
  return data.results;
};

export const useChildProficiency = (childId: number | undefined) =>
  useQuery<StudentProficiency[]>({
    queryKey: ['parent', 'proficiency', childId],
    queryFn: () => fetchChildProficiency(childId!),
    enabled: !!childId,
    staleTime: 2 * 60 * 1000,
  });
