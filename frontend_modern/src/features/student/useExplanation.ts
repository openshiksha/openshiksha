import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface SubpartExplanation {
  id: number;
  question_subpart: number;
  question_text: string;
  subpart_index: number;
  submission: number | null;
  student_answer: unknown;
  is_correct: boolean;
  explanation_text: string;
  language: string;
  grade_level: number;
  model_used: string;
  generated_at: string;
}

/**
 * Explanations are generated asynchronously (POST /generate/ returns 202 and
 * queues a Celery task), so the consumer polls this list query until the row
 * for the subpart appears. Explanations persist server-side — once one exists
 * for a subpart it is shown directly and never re-generated.
 */
export const useExplanationList = (subpartId: number, enabled: boolean) =>
  useQuery<SubpartExplanation[]>({
    queryKey: ['ai', 'explanations', subpartId],
    queryFn: async () => {
      const { data } = await apiClient.get<
        SubpartExplanation[] | { results: SubpartExplanation[] }
      >(`/ai/explanations/?subpart=${subpartId}`);
      return Array.isArray(data) ? data : data.results ?? [];
    },
    enabled,
    staleTime: Infinity,
  });

export interface GenerateExplanationPayload {
  subpart_id: number;
  student_answer: string;
  is_correct: boolean;
}

export const useGenerateExplanation = () =>
  useMutation<void, Error, GenerateExplanationPayload>({
    mutationFn: async (payload) => {
      await apiClient.post('/ai/explanations/generate/', payload);
    },
  });
