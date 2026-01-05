import { useQuery } from '@tanstack/react-query';
import { authApi } from '@/api/auth';

export const useAuth = () => {
  const { data: isValid, isLoading } = useQuery({
    queryKey: ['auth', 'verify'],
    queryFn: () => authApi.verifyToken(),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  return {
    isAuthenticated: isValid === true,
    isLoading,
  };
};
