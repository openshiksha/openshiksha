import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { HintSequence } from '@/types/index';

interface GenerateHintsRequest {
  subpart_id: number;
  num_hints?: number;
}

/**
 * Fetch (or generate-and-cache) the progressive AI hint sequence for a subpart.
 *
 * The backend caches one sequence per subpart, so repeated calls across students
 * reuse the same hints rather than re-invoking the LLM. The returned payload
 * never includes the correct answer.
 */
const generateHints = async (data: GenerateHintsRequest): Promise<HintSequence> => {
  const response = await apiClient.post<HintSequence>('/ai/hints/generate/', data);
  return response.data;
};

export const useHints = () =>
  useMutation<HintSequence, Error, GenerateHintsRequest>({
    mutationFn: generateHints,
  });
