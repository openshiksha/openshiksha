import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface Announcement {
  id: number;
  subject_room: number;
  subject_room_display: string;
  author: number | null;
  author_name: string;
  message: string;
  is_active: boolean;
  created_at: string;
}

interface Paginated<T> {
  results: T[];
}

const fetchAnnouncements = async (): Promise<Announcement[]> => {
  const response = await apiClient.get<Paginated<Announcement>>('/announcements/');
  return response.data.results ?? [];
};

export const useAnnouncements = () =>
  useQuery<Announcement[]>({
    queryKey: ['announcements'],
    queryFn: fetchAnnouncements,
    staleTime: 2 * 60 * 1000,
  });
