import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { ResyncDiff } from './useAssignmentResync';

export interface VersionSummary {
  id: number;
  version_number: number;
  content_hash: string;
  created_at: string;
  created_by_name: string | null;
  question_count: number;
  assignment_count: number;
}

interface VersionsResponse {
  problem_set_id: number;
  versions: VersionSummary[];
}

export interface VersionDiffResponse {
  target: { id: number; version_number: number };
  against: { id: number; version_number: number } | null;
  diff: ResyncDiff;
}

const fetchVersions = async (problemSetId: number): Promise<VersionsResponse> => {
  const res = await apiClient.get<VersionsResponse>(`/problem-sets/${problemSetId}/versions/`);
  return res.data;
};

export const useProblemSetVersions = (problemSetId: number | null) => {
  return useQuery<VersionsResponse>({
    queryKey: ['problem-set-versions', problemSetId],
    queryFn: () => fetchVersions(problemSetId as number),
    enabled: problemSetId != null,
    staleTime: 30 * 1000,
  });
};

const fetchVersionDiff = async (
  problemSetId: number,
  targetId: number,
  againstId: number | null,
): Promise<VersionDiffResponse> => {
  const url =
    againstId != null
      ? `/problem-sets/${problemSetId}/versions/${targetId}/diff/?against=${againstId}`
      : `/problem-sets/${problemSetId}/versions/${targetId}/diff/`;
  const res = await apiClient.get<VersionDiffResponse>(url);
  return res.data;
};

export const useVersionDiff = (
  problemSetId: number | null,
  targetId: number | null,
  againstId: number | null,
) => {
  return useQuery<VersionDiffResponse>({
    queryKey: ['problem-set-version-diff', problemSetId, targetId, againstId],
    queryFn: () => fetchVersionDiff(problemSetId as number, targetId as number, againstId),
    enabled: problemSetId != null && targetId != null,
    staleTime: 60 * 1000,
  });
};
