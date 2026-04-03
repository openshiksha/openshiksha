import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse, StudentProficiency } from '@/types/index';

const fetchProficiency = async (): Promise<StudentProficiency[]> => {
  const response = await apiClient.get<PaginatedResponse<StudentProficiency>>('/proficiency/');
  return response.data.results;
};

export const useProficiency = () => {
  return useQuery<StudentProficiency[]>({
    queryKey: ['proficiency'],
    queryFn: fetchProficiency,
    staleTime: 5 * 60 * 1000,
  });
};
