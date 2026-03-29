/**
 * Core type definitions for OpenShiksha
 */

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
}

export enum UserRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
  PARENT = 'parent',
  ADMIN = 'admin',
  OPEN_STUDENT = 'open_student',
}

export interface QuestionTag {
  id: number;
  name: string;
  tag_type: 'concept' | 'skill' | 'difficulty' | 'special';
}

export interface QuestionSubpart {
  id: number;
  index: number;
  tags: QuestionTag[];
}

export interface Question {
  id: number;
  standard: number;
  subject: number;
  chapter: number;
  question_type: 'mcq' | 'fill_blank' | 'matching' | 'multi_select' | 'numeric';
  difficulty: number;
  tags: QuestionTag[];
  subparts: QuestionSubpart[];
  is_active: boolean;
  created_at: string;
}

export interface SubjectRoomTeacher {
  id: number;
  first_name: string;
  last_name: string;
}

export interface SubjectRoom {
  id: number;
  classroom: number;
  subject: { id: number; name: string };
  teacher: SubjectRoomTeacher;
  is_active: boolean;
  student_count: number;
}

export interface ProblemSet {
  id: number;
  title: string;
  description: string;
  chapter: { id: number; name: string };
  subject: { id: number; name: string };
  standard: { id: number; name: string };
  question_count: number;
  estimated_minutes: number | null;
  is_active: boolean;
}

export interface Submission {
  id: number;
  assignment: number;
  student: number;
  score: number | null;
  completion: number;
  answers: Record<string, unknown>;
  submitted_at: string | null;
  is_revised: boolean;
  created_at: string;
  updated_at: string;
}

export interface Assignment {
  id: number;
  subject_room: number;
  subject_room_display: string;
  problem_set: ProblemSet;
  assigned_by: number;
  assigned_at: string;
  due_at: string;
  number: number;
  average_score: number | null;
  completion_rate: number | null;
  my_submission?: Submission | null;
}

export interface ApiError {
  detail: string;
  code?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
