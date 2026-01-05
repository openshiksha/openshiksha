/**
 * Core type definitions for OpenShiksha
 *
 * These will expand as we implement features in each phase
 */

// User and Auth types
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
}

// Question and Assignment types (placeholders - will be detailed in Phase 1)
export interface Question {
  id: number;
  // Will add variable constraint types here
}

export interface Assignment {
  id: number;
  title: string;
  due_date: string;
  // More fields to come
}

// API Response types
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
