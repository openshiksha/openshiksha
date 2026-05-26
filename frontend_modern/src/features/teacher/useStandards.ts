import { useQuery } from '@tanstack/react-query';

export interface Standard {
  id: number;
  number: number;
  description: string;
}

export const useStandards = () => {
  return useQuery<Standard[]>({
    queryKey: ['standards'],
    queryFn: async () =>
      Array.from({ length: 12 }, (_, i) => ({
        id: i + 1,
        number: i + 1,
        description: `Grade ${i + 1}`,
      })),
    staleTime: Infinity,
  });
};
