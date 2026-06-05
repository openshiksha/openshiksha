import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { TutorConversation } from '@/types/index';

interface StartTutorRequest {
  subpart_id?: number;
  message: string;
}

interface PostTutorMessageRequest {
  conversationId: number;
  message: string;
}

/**
 * Start a new AI Tutor conversation, optionally anchored to a question subpart.
 *
 * The tutor guides Socratically and never reveals the answer; the returned
 * conversation includes the student's message and the tutor's first reply.
 */
const startConversation = async (data: StartTutorRequest): Promise<TutorConversation> => {
  const response = await apiClient.post<TutorConversation>('/ai/tutor/', data);
  return response.data;
};

/** Post a follow-up message to an existing conversation and get the tutor's reply. */
const postMessage = async ({
  conversationId,
  message,
}: PostTutorMessageRequest): Promise<TutorConversation> => {
  const response = await apiClient.post<TutorConversation>(
    `/ai/tutor/${conversationId}/message/`,
    { message },
  );
  return response.data;
};

export const useStartTutor = () =>
  useMutation<TutorConversation, Error, StartTutorRequest>({
    mutationFn: startConversation,
  });

export const useTutorMessage = () =>
  useMutation<TutorConversation, Error, PostTutorMessageRequest>({
    mutationFn: postMessage,
  });
