import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types/index';

export interface LearningPathStep {
  id: number;
  position: number;
  knowledge_node: number;
  chapter_name: string;
  subject_name: string;
  problem_set: number | null;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  status_display: string;
  is_review: boolean;
  score_when_completed: number | null;
  completed_at: string | null;
}

export interface LearningPath {
  id: number;
  subject_room: number;
  status: 'active' | 'completed' | 'paused';
  status_display: string;
  total_steps: number;
  completed_steps: number;
  progress_pct: number;
  steps: LearningPathStep[];
  generated_at: string;
  updated_at: string;
}

const fetchLearningPaths = async (): Promise<LearningPath[]> => {
  const { data } = await apiClient.get<PaginatedResponse<LearningPath>>('/ai/learning-paths/');
  return data.results;
};

export const useLearningPaths = () =>
  useQuery<LearningPath[]>({
    queryKey: ['ai', 'learning-paths'],
    queryFn: fetchLearningPaths,
    staleTime: 5 * 60 * 1000,
  });
