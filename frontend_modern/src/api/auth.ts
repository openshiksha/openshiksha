import { apiClient } from './client';
import type { RegisterOpenRequest, RegisterResponse, RegisterSchoolRequest, User } from '@/types/index';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/users/me/');
    return response.data;
  },

  verifyToken: async (): Promise<boolean> => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return false;
      await apiClient.post('/auth/verify/', { token });
      return true;
    } catch {
      return false;
    }
  },

  registerOpen: async (data: RegisterOpenRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/auth/register/open/', data);
    return response.data;
  },

  registerSchool: async (data: RegisterSchoolRequest): Promise<RegisterResponse> => {
    const response = await apiClient.post<RegisterResponse>('/auth/register/school/', data);
    return response.data;
  },

  updateProfile: async (
    data: Partial<
      Pick<
        User,
        'first_name' | 'last_name' | 'email' | 'phone_number' | 'email_reminders_opt_out' | 'preferred_language'
      >
    >
  ): Promise<User> => {
    const response = await apiClient.patch<User>('/users/me/profile/', data);
    return response.data;
  },

  changePassword: async (data: ChangePasswordRequest): Promise<{ detail: string }> => {
    const response = await apiClient.post<{ detail: string }>('/users/me/password/', data);
    return response.data;
  },
};
