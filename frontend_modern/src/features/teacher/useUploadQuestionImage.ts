import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface UploadQuestionImageResponse {
  image_url: string;
}

const uploadQuestionImage = async (file: File): Promise<UploadQuestionImageResponse> => {
  const body = new FormData();
  body.append('image', file);
  const response = await apiClient.post<UploadQuestionImageResponse>('/questions/upload-image/', body);
  return response.data;
};

export const useUploadQuestionImage = () =>
  useMutation<UploadQuestionImageResponse, Error, File>({
    mutationFn: uploadQuestionImage,
  });
