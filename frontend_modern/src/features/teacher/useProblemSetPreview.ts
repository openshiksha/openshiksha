import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { Question } from '@/types/index';

/**
 * A problem set rendered exactly as a student sees it — correct answers
 * stripped, `{{var}}` tokens substituted, MCQ options shuffled. Backed by
 * `GET /problem-sets/<id>/preview/` (teacher-only, read-only).
 */
export interface ProblemSetStudentPreview {
  id: number;
  title: string;
  description: string;
  number: number;
  subject_name: string;
  chapter_name: string;
  estimated_minutes: number | null;
  question_count: number;
  questions: Question[];
}

const fetchPreview = async (id: number): Promise<ProblemSetStudentPreview> => {
  const res = await apiClient.get<ProblemSetStudentPreview>(`/problem-sets/${id}/preview/`);
  return res.data;
};

export const useProblemSetPreview = (id: number | null) => {
  return useQuery<ProblemSetStudentPreview>({
    queryKey: ['problem-set-preview', id],
    queryFn: () => fetchPreview(id as number),
    enabled: id != null,
    staleTime: 60 * 1000,
  });
};
