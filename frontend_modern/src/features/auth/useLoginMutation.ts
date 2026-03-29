import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import type { LoginRequest } from '@/api/auth';
import { UserRole } from '@/types/index';

export const useLoginMutation = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const tokens = await authApi.login(credentials);
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      return tokens;
    },
    onSuccess: async () => {
      // Invalidate auth queries so useAuth re-fetches
      await queryClient.invalidateQueries({ queryKey: ['auth'] });

      // Fetch user to determine where to redirect
      try {
        const user = await authApi.getCurrentUser();
        if (user.role === UserRole.TEACHER) {
          navigate('/teacher');
        } else {
          navigate('/student');
        }
      } catch {
        navigate('/student');
      }
    },
  });
};
