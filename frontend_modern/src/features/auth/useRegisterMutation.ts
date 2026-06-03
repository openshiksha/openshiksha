import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '@/api/auth';
import type { RegisterOpenRequest, RegisterSchoolRequest } from '@/types/index';

function storeTokensAndNavigate(
  access: string,
  refresh: string,
  role: string,
  navigate: ReturnType<typeof useNavigate>,
) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  const dest =
    role === 'teacher' ? '/teacher' : role === 'open_student' ? '/student/browse' : '/student';
  navigate(dest, { replace: true });
}

export const useRegisterOpenMutation = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RegisterOpenRequest) => authApi.registerOpen(data),
    onSuccess: async (res) => {
      storeTokensAndNavigate(res.access, res.refresh, res.user.role, navigate);
      await queryClient.invalidateQueries({ queryKey: ['auth'] });
    },
  });
};

export const useRegisterSchoolMutation = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RegisterSchoolRequest) => authApi.registerSchool(data),
    onSuccess: async (res) => {
      storeTokensAndNavigate(res.access, res.refresh, res.user.role, navigate);
      await queryClient.invalidateQueries({ queryKey: ['auth'] });
    },
  });
};
