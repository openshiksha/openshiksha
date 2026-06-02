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
  grade?: number | null;
  phone_number?: string;
  email_reminders_opt_out?: boolean;
}

export interface ClassroomInviteCode {
  id: number;
  code: string;
  classroom_id: number;
  classroom_name: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
}

export interface BrowseChapter {
  id: number;
  name: string;
  subject_id: number;
  subject: string;
  standard_id: number;
  standard: number;
  question_count: number;
}

export interface RegisterOpenRequest {
  username: string;
  password: string;
  email?: string;
  first_name?: string;
  last_name?: string;
}

export interface RegisterSchoolRequest extends RegisterOpenRequest {
  join_code: string;
}

export interface RegisterResponse {
  access: string;
  refresh: string;
  user: {
    id: number;
    username: string;
    role: string;
    first_name: string;
    last_name: string;
    email: string;
  };
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

export interface MCQOption {
  key: string;
  text: string;
}

/** Answer types a single subpart can have (mirrors backend QuestionType). */
export type SubpartType = 'mcq' | 'fill_blank' | 'matching' | 'multi_select' | 'numeric' | 'short_answer';

export interface QuestionSubpart {
  id: number;
  index: number;
  /**
   * Per-subpart answer type (M7-03). Blank ('') for hand-authored rows that
   * predate the field — callers fall back to the parent Question.question_type.
   */
  subpart_type?: SubpartType | '';
  tags: QuestionTag[];
  question_text: string;
  options: MCQOption[] | null;
  image_url?: string;
  solution_text?: string;
  hint_text?: string;
}

export interface AIHint {
  level: number;
  text: string;
}

export interface HintSequence {
  id: number;
  question_subpart: number;
  hints: AIHint[];
  hint_count: number;
  grade_level: number;
  generated_at: string;
}


export interface Question {
  id: number;
  standard: number;
  standard_number?: number;
  subject: number;
  subject_name?: string;
  chapter: number;
  chapter_name?: string;
  /** 'compound' = subparts have heterogeneous types (M7-03). */
  question_type: SubpartType | 'compound';
  question_type_display?: string;
  difficulty: number;
  /** Optional shared stem rendered once above the subparts (M7-07). */
  stem_text?: string;
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
  is_remedial: boolean;
  source_assignment: number | null;
}

export interface ProblemSetWithQuestions extends ProblemSet {
  questions: Question[];
}

export interface AssignmentDetail extends Assignment {
  problem_set: ProblemSetWithQuestions;
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
  submission_count: number;
  student_count: number;
  my_submission?: Submission | null;
  child_submission_status?: 'submitted' | 'not_submitted' | null;
}

export interface Subject {
  id: number;
  name: string;
  description: string;
}

export interface ChapterItem {
  id: number;
  name: string;
  subject: number;
  subject_name: string;
  standard: number;
  standard_number: number;
  order: number;
}

export interface StudentProficiency {
  id: number;
  question_tag: number;
  tag_name: string;
  tag_type: string;
  subject_name: string;
  subject_room: number;
  classroom_display: string;
  score: number;
  rate: number;
  percentile: number;
  tick_count: number;
  updated_at: string;
}

export interface GeneratedQuestionDraft {
  question_text: string;
  options: MCQOption[] | null;
  correct_answer: string;
  variable_constraints: Record<string, { min: number; max: number; integer: boolean }> | null;
  suggested_tags: string[];
  solution?: string;
}

export interface GenerateQuestionsRequest {
  topic: string;
  chapter_id: number;
  question_type: 'mcq' | 'fill_blank' | 'numeric' | 'multi_select';
  difficulty: number;
  count: number;
}

export interface QuestionSubpartWrite {
  index: number;
  question_text: string;
  options: MCQOption[] | null;
  correct_answer: Record<string, unknown>;
  variable_constraints?: Record<string, { min: number; max: number; integer: boolean }> | null;
  image_url?: string;
  solution_text?: string;
  hint_text?: string;
}

export interface QuestionCreate {
  standard: number;
  subject: number;
  chapter: number;
  question_type: 'mcq' | 'fill_blank' | 'matching' | 'multi_select' | 'numeric';
  difficulty: number;
  tag_ids?: number[];
  subparts: QuestionSubpartWrite[];
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
