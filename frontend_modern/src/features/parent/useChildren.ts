import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { User } from '@/types/index';

const fetchChildren = async (): Promise<User[]> => {
  const { data } = await apiClient.get<User[]>('/users/me/children/');
  return Array.isArray(data) ? data : [];
};

export const useChildren = () =>
  useQuery<User[]>({
    queryKey: ['parent', 'children'],
    queryFn: fetchChildren,
    staleTime: 5 * 60 * 1000,
  });
