import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse, Subject } from '@/types/index';

const fetchSubjects = async (): Promise<Subject[]> => {
  const response = await apiClient.get<PaginatedResponse<Subject>>('/subjects/');
  return response.data.results;
};

export const useSubjects = () => {
  return useQuery<Subject[]>({
    queryKey: ['subjects'],
    queryFn: fetchSubjects,
    staleTime: 10 * 60 * 1000,
  });
};
