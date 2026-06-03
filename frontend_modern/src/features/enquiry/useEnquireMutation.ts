import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface EnquiryRequest {
  name: string;
  school: string;
  email: string;
  phone?: string;
  message?: string;
}

export const useEnquireMutation = () =>
  useMutation({
    mutationFn: (data: EnquiryRequest) =>
      apiClient.post('/enquire/', data).then((r) => r.data),
  });
