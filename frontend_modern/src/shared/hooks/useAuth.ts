import { useQuery, useQueryClient, useIsRestoring } from '@tanstack/react-query';
import { authApi } from '@/api/auth';
import type { User } from '@/types/index';

export const useAuth = () => {
  const queryClient = useQueryClient();

  // While PersistQueryClientProvider rehydrates the cache from IndexedDB (MSO-4),
  // queries are held *idle*: `status: 'pending'` but `fetchStatus: 'idle'`. RQ's
  // `isLoading` (= isPending && isFetching) is therefore FALSE during the restore
  // window even though `isValid` is still undefined. Gating the app on `isLoading`
  // would render an unauthenticated tree for the first paint and bounce a hard
  // deep-link (e.g. /teacher/questions) through ProtectedRoute → /login, from
  // where LoginPage then redirects the (now-verified) user to their role home —
  // silently dropping the deep link. We therefore gate on `isPending` (status ===
  // 'pending', true for the whole restore→fetch window) plus `isRestoring`, so
  // the bootstrap stays "loading" until verify actually resolves.
  const isRestoring = useIsRestoring();

  const { data: isValid, isPending: isVerifying } = useQuery({
    queryKey: ['auth', 'verify'],
    queryFn: () => authApi.verifyToken(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const isAuthenticated = isValid === true;

  const { data: user, isPending: isLoadingUser } = useQuery<User>({
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
    isLoading: isRestoring || isVerifying || (isAuthenticated && isLoadingUser),
    user: user ?? null,
    logout,
  };
};
