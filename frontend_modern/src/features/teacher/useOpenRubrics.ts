import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface RubricCriterion {
  label: string;
  description?: string;
  marks: number;
}

/** Mirrors OpenResponseRubricSerializer (backend/openshiksha/apps/ai/serializers.py). */
export interface OpenResponseRubric {
  id: number;
  subpart: number;
  question_text: string;
  max_marks: number;
  model_answer: string;
  criteria: RubricCriterion[];
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

const rubricKey = (subpartId: number) => ['ai', 'open-rubrics', subpartId];

/** One rubric per subpart (OneToOne server-side) — resolve to it or null. */
export const useRubricForSubpart = (subpartId: number | null) =>
  useQuery<OpenResponseRubric | null>({
    queryKey: rubricKey(subpartId ?? 0),
    queryFn: async () => {
      const { data } = await apiClient.get<
        OpenResponseRubric[] | { results: OpenResponseRubric[] }
      >(`/ai/open-rubrics/?subpart=${subpartId}`);
      const rows = Array.isArray(data) ? data : (data.results ?? []);
      return rows[0] ?? null;
    },
    enabled: subpartId != null,
    staleTime: 60 * 1000,
  });

export interface RubricPayload {
  subpart: number;
  max_marks: number;
  model_answer: string;
  criteria: RubricCriterion[];
}

/** Create when the subpart has no rubric yet, PATCH the existing one otherwise. */
export const useSaveRubric = () => {
  const queryClient = useQueryClient();
  return useMutation<OpenResponseRubric, Error, { existingId: number | null } & RubricPayload>({
    mutationFn: async ({ existingId, ...payload }) => {
      const { data } = existingId
        ? await apiClient.patch<OpenResponseRubric>(`/ai/open-rubrics/${existingId}/`, payload)
        : await apiClient.post<OpenResponseRubric>('/ai/open-rubrics/', payload);
      return data;
    },
    onSuccess: (rubric) => {
      queryClient.invalidateQueries({ queryKey: rubricKey(rubric.subpart) });
    },
  });
};

export interface RoomStudent {
  id: number;
  full_name: string;
  username: string;
}

/** Roster of a subject room — teacher-only picker data. */
export const useRoomStudents = (roomId: number | null) =>
  useQuery<RoomStudent[]>({
    queryKey: ['subject-rooms', roomId, 'students'],
    queryFn: async () => {
      const { data } = await apiClient.get<{ results: RoomStudent[] }>(
        `/subject-rooms/${roomId}/students/`
      );
      return data.results;
    },
    enabled: roomId != null,
    staleTime: 5 * 60 * 1000,
  });

export interface ShortAnswerSubpartOption {
  subpartId: number;
  questionId: number;
  label: string;
}

interface QuestionRow {
  id: number;
  subparts: Array<{ id: number; question_text: string }>;
}

/**
 * The teacher's short-answer subparts, flattened for a picker. Only
 * short-answer questions can carry a rubric / be AI-graded as open responses.
 */
export const useShortAnswerSubparts = (enabled = true) =>
  useQuery<ShortAnswerSubpartOption[]>({
    queryKey: ['questions', 'short-answer-subparts'],
    queryFn: async () => {
      const { data } = await apiClient.get<QuestionRow[] | { results: QuestionRow[] }>(
        '/questions/?question_type=short_answer'
      );
      const rows = Array.isArray(data) ? data : (data.results ?? []);
      return rows.flatMap((q) =>
        q.subparts.map((sp) => ({
          subpartId: sp.id,
          questionId: q.id,
          label:
            sp.question_text.length > 90 ? `${sp.question_text.slice(0, 90)}…` : sp.question_text,
        }))
      );
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });

export const useSubmitOpenResponse = () => {
  const queryClient = useQueryClient();
  return useMutation<
    unknown,
    Error,
    { subpart_id: number; student_id: number; subject_room_id: number; response_text: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post('/ai/open-grades/submit/', payload);
      return data;
    },
    onSuccess: () => {
      // The new pending row should appear in every grading-queue view.
      queryClient.invalidateQueries({ queryKey: ['ai', 'open-grades'] });
    },
  });
};
