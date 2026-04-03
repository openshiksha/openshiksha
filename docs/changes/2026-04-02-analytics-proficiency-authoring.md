# Teacher Analytics, Student Proficiency Page, Question Authoring UI

**Date**: 2026-04-02
**Branch**: `feat/2026-04-02-analytics-proficiency-authoring`
**PR**: #66
**Classification**: New (all three features)

---

## Summary

Surfaces the platform's analytics data that was already being generated (grading pipeline, StudentProficiency model) but going nowhere visible, and unblocks teachers from Django admin dependency for question creation.

---

## What was implemented

### Priority 1: Teacher Assignment Analytics

The `TeacherDashboard` previously showed only subject rooms. Teachers had no way to see which assignments were live, how many students submitted, or what the avg score was.

**Backend:**
- `AssignmentSerializer`: added `submission_count` (live count) and `student_count` (subject room enrollment) as `SerializerMethodField`s
- Performance note: adds 2 queries per assignment in list view — acceptable for now. Future optimization: `annotate()` on queryset.

**Frontend:**
- `TeacherDashboard`: new Assignments section below Subject Rooms
- Each row: problem set title, subject room display, due date (overdue in red), `X/Y submitted`, avg score (shown when available), submission progress bar
- `useTeacherAssignments`: hook for `GET /api/assignments/`
- "+ New Question" button added to dashboard header

### Priority 2: Student Proficiency Page (`/student/proficiency`)

Students completed assignments, grading ran, `StudentProficiency` got updated — but nothing surfaced to the student. This closes that gap.

**Backend:**
- `StudentProficiencyViewSet`: read-only, `IsStudent` permission enforced
- `GET /api/v1/proficiency/` returns all `StudentProficiency` records for the current student
- `StudentProficiencySerializer`: exposes `tag_name`, `tag_type`, `subject_name`, `subject_room`, `classroom_display`, `score`, `rate`, `percentile`, `tick_count`, `updated_at`
- Records ordered by subject name then tag name

**Frontend:**
- `ProficiencyPage`: grouped by subject room → list of tags with visual progress bars
- Color coding: green (≥70%), yellow (≥40%), red (<40%)
- Shows attempt count ("Based on X questions")
- Empty state when no submissions yet
- `useProficiency`: hook for `GET /api/v1/proficiency/`
- `StudentDashboard`: "My Progress →" link added to page header
- Route: `/student/proficiency`

**Legacy comparison**: Legacy showed a single subject-level score on a server-rendered profile page. This shows per-tag breakdown, is visual, and updates after every grading.

### Priority 3: Question Authoring UI Phase 1 (`/teacher/questions/new`)

Teachers previously had to use Django admin to create questions — a hard blocker for real-world teacher onboarding.

**Backend:**
- `QuestionViewSet`: promoted from `ReadOnlyModelViewSet` to `ModelViewSet`; write actions (`create`, `update`, `partial_update`, `destroy`) gated to `IsTeacher`
- `QuestionWriteSerializer`: accepts nested `subparts`, validates at least one subpart exists, assigns `created_by` and school on `perform_create`
- `QuestionSubpartWriteSerializer`: creates subparts as nested objects
- New `SubjectViewSet` (read-only): `GET /api/v1/subjects/` — used for chapter picker
- New `ChapterViewSet` (read-only): `GET /api/v1/chapters/?subject=<id>` — filtered chapter list
- Router: registered `subjects`, `chapters`, `proficiency`

**Frontend:**
- `CreateQuestionPage`:
  - Subject dropdown (from teacher's subject rooms)
  - Chapter dropdown (filtered by selected subject)
  - Difficulty picker (1–5 stars)
  - Multi-subpart tabs ("Part A", "Part B", ...) — add/remove subparts
  - Question type selector (MCQ, numeric, fill blank, multi-select)
  - Question text textarea (LaTeX-aware)
  - **Live KaTeX preview** — renders `$...$` and `$$...$$` in real-time as teacher types
  - MCQ options form (A/B/C/D) when MCQ type selected
  - Correct answer selector
  - Success state with "Create another" / "Back to dashboard" options
- Hooks: `useCreateQuestion`, `useChapters`, `useSubjects`
- Route: `/teacher/questions/new`

**Legacy comparison**: Legacy `sphinx/` stored content in Cabinet (external filesystem). This stores directly in DB (no external dependency). Adds live KaTeX preview — didn't exist in legacy.

---

## Technical details

### Files changed
**Backend:**
- `apps/api/serializers/core.py` — StandardSerializer, SubjectSerializer, ChapterSerializer, QuestionSubpartWriteSerializer, QuestionWriteSerializer added; AssignmentSerializer extended; StudentProficiencySerializer added
- `apps/api/serializers/__init__.py` — exports updated
- `apps/api/views/core.py` — SubjectViewSet, ChapterViewSet added; QuestionViewSet made writable; StudentProficiencyViewSet added
- `apps/api/urls.py` — subjects, chapters, proficiency routes registered

**Frontend:**
- `src/types/index.ts` — Assignment extended; Subject, ChapterItem, StudentProficiency, QuestionSubpartWrite, QuestionCreate types added
- `src/features/teacher/TeacherDashboard.tsx` — refactored with assignments section
- `src/features/teacher/useTeacherAssignments.ts` — new
- `src/features/teacher/CreateQuestionPage.tsx` — new
- `src/features/teacher/useCreateQuestion.ts` — new
- `src/features/teacher/useChapters.ts` — new
- `src/features/teacher/useSubjects.ts` — new
- `src/features/student/ProficiencyPage.tsx` — new
- `src/features/student/useProficiency.ts` — new
- `src/features/student/StudentDashboard.tsx` — "My Progress →" link
- `src/App.tsx` — `/student/proficiency` and `/teacher/questions/new` routes

**Tests:**
- `apps/api/tests/test_analytics_api.py` — 16 tests

---

## Tests written

`test_analytics_api.py` covers:
1. Assignment analytics fields: teacher and student both receive `submission_count` and `student_count`; count increments when student submits
2. StudentProficiencyViewSet: unauthenticated 401, teacher 403, student sees own records only, correct field values, isolation between students
3. QuestionViewSet write: teacher can POST with nested subparts; student 403; empty subparts 400
4. Subject/Chapter endpoints: list, filter by subject, unauthenticated 401

Frontend: 11/11 Vitest tests pass; 0 TypeScript errors; 0 ESLint warnings.

---

## Migration notes

No new migrations required — no model changes. All new functionality uses existing models (`StudentProficiency`, `Question`, `QuestionSubpart`, `Chapter`, `Subject`).

---

## Next steps

1. **Teacher assignment detail page** — per-student submission breakdown using existing `GET /api/assignments/{id}/submissions/`
2. **Question authoring Phase 2** — image upload, variable constraints (Croupier integration)
3. **Performance optimization** — annotate `submission_count`/`student_count` on queryset for teachers with many assignments (current: 2 queries per assignment)
4. **Proficiency trends** — score history over time (requires `StudentProficiency` versioning or separate audit table)
5. **LearningGap integration** — highlight chapters with `GapSeverity.SEVERE` on proficiency page
