import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface SchoolPerson {
  id: number;
  full_name: string;
  email: string;
}

const fetchTeachers = async (): Promise<SchoolPerson[]> => {
  const response = await apiClient.get<SchoolPerson[]>('/users/school-teachers/');
  return response.data;
};

const fetchStudents = async (): Promise<SchoolPerson[]> => {
  const response = await apiClient.get<SchoolPerson[]>('/users/school-students/');
  return response.data;
};

export const useSchoolTeachers = () =>
  useQuery<SchoolPerson[]>({
    queryKey: ['admin', 'school-teachers'],
    queryFn: fetchTeachers,
    staleTime: 5 * 60 * 1000,
  });

export const useSchoolStudents = () =>
  useQuery<SchoolPerson[]>({
    queryKey: ['admin', 'school-students'],
    queryFn: fetchStudents,
    staleTime: 5 * 60 * 1000,
  });
