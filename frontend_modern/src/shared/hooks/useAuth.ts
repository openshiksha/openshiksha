import { useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import type { User } from '@/types/index';

export const useAuth = () => {
  const queryClient = useQueryClient();

  const { data: isValid, isLoading: isVerifying } = useQuery({
    queryKey: ['auth', 'verify'],
    queryFn: () => authApi.verifyToken(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const isAuthenticated = isValid === true;

  const { data: user, isLoading: isLoadingUser } = useQuery<User>({
    queryKey: ['auth', 'me'],
    queryFn: () => authApi.getCurrentUser(),
    enabled: isAuthenticated,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const logout = () => {
    authApi.logout();
    queryClient.clear();
    window.location.href = '/login';
  };

  return {
    isAuthenticated,
    isLoading: isVerifying || (isAuthenticated && isLoadingUser),
    user: user ?? null,
    logout,
  };
};
