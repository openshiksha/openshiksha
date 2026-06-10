import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface MisconceptionCluster {
  id: number;
  subject_room: number;
  subject_name: string;
  misconception_label: string;
  student_count: number;
  occurrence_count: number;
  sample_diagnosis: string;
  sample_remediation_tip: string;
  window_start: string;
  last_seen: string;
  refreshed_at: string;
}

const fetchClusters = async (subjectRoomId: number): Promise<MisconceptionCluster[]> => {
  const { data } = await apiClient.get<
    MisconceptionCluster[] | { results: MisconceptionCluster[] }
  >(`/ai/misconception-clusters/?subject_room=${subjectRoomId}`);
  return Array.isArray(data) ? data : data.results ?? [];
};

export const useMisconceptionClusters = (subjectRoomId: number, enabled: boolean) =>
  useQuery<MisconceptionCluster[]>({
    queryKey: ['ai', 'misconception-clusters', subjectRoomId],
    queryFn: () => fetchClusters(subjectRoomId),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

export const useRefreshMisconceptionClusters = (subjectRoomId: number) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/ai/misconception-clusters/refresh/', {
        subject_room_id: subjectRoomId,
      });
    },
    onSuccess: () => {
      // Recompute is async on the server; refetch shortly after to pick up new rows.
      setTimeout(() => {
        queryClient.invalidateQueries({
          queryKey: ['ai', 'misconception-clusters', subjectRoomId],
        });
      }, 2500);
    },
  });
};
