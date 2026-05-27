import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface TeacherProblemSet {
  id: number;
  title: string;
  description: string;
  number: number;
  standard: number;
  subject: number;
  subject_name: string;
  chapter: number;
  chapter_name: string;
  question_count: number;
  estimated_minutes: number | null;
  is_active: boolean;
}

const fetchProblemSets = async (subjectId?: number): Promise<TeacherProblemSet[]> => {
  const params = subjectId ? `?subject=${subjectId}` : '';
  const response = await apiClient.get<PaginatedResponse<TeacherProblemSet>>(
    `/problem-sets/${params}`
  );
  return response.data.results;
};

export const useProblemSets = (subjectId?: number | null) => {
  return useQuery<TeacherProblemSet[]>({
    queryKey: ['problem-sets', subjectId ?? null],
    queryFn: () => fetchProblemSets(subjectId ?? undefined),
    staleTime: 5 * 60 * 1000,
  });
};
