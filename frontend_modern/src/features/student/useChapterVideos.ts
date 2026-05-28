import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface Video {
  id: number;
  chapter: number;
  chapter_name: string;
  title: string;
  embed_url: string;
  description: string;
  order: number;
  is_active: boolean;
  created_at: string;
}

interface Paginated<T> {
  results: T[];
}

const fetchChapterVideos = async (chapterId: number): Promise<Video[]> => {
  const response = await apiClient.get<Paginated<Video>>('/videos/', {
    params: { chapter: chapterId },
  });
  return response.data.results ?? [];
};

export const useChapterVideos = (chapterId: number | undefined) =>
  useQuery<Video[]>({
    queryKey: ['chapter-videos', chapterId],
    queryFn: () => fetchChapterVideos(chapterId as number),
    enabled: !!chapterId,
    staleTime: 5 * 60 * 1000,
  });
