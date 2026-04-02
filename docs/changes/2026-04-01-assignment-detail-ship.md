# Assignment Detail Ship — 2026-04-01

## Summary

Ships the full student assignment practice loop end-to-end: students can now navigate to an assignment, read LaTeX-rendered questions, answer MCQ/numeric/fill-blank inputs with debounced auto-save, and submit for grading. Includes a seed command for instant demo setup and a teacher assignment creation UI.

## Classification

| Change | Type |
|--------|------|
| `question_text` + `options` on `QuestionSubpart` | **Improve** — removes cabinet dependency for content |
| Student assignment detail page + KaTeX rendering | **Improve** — React SPA vs legacy full-page-reload |
| Submission filter bug fix | **Fix** |
| `seed_demo_data` management command | **New** |
| Teacher dashboard + assignment creation UI | **New** |
| Frontend CI pipeline | **New** |

## Legacy Reference

### Question content (QuestionSubpart)
- **Legacy did**: Question text stored in cabinet (external service), fetched at render time via cabinet API. No content in Django models.
- **What was limited**: Tightly coupled to cabinet service; offline/demo mode impossible; no content versioning.
- **What we improved**: `question_text` (LaTeX/plain text) and `options` (MCQ choices as JSON) stored directly on `QuestionSubpart`. In production these get populated on cabinet import. In dev, `seed_demo_data` provides real LaTeX content instantly.

### Assignment detail / answer submission
- **Legacy did**: Django template rendering, form POST per answer, full-page reload, server-side session tracking.
- **What was limited**: No auto-save; poor mobile UX; no real-time feedback; full page reload per answer.
- **What we improved**: Single-page React with debounced auto-save (2s), optimistic UI, KaTeX rendering, answer state persisted in `Submission.answers` JSON.

### Teacher assignment creation
- **Legacy did**: Django admin or custom server-rendered teacher portal.
- **What we improved**: API-first React form. Same `POST /api/v1/assignments/` endpoint will work for future mobile apps.

## Technical Details

### Backend changes

**`QuestionSubpart` model** (`0003` migration):
- `question_text: TextField` — LaTeX or plain text, `$...$` for inline math
- `options: JSONField` — `[{"key": "A", "text": "..."}, ...]` for MCQ, null for others

**`SubmissionViewSet.get_queryset()`** fix:
- Added `?assignment=<id>` filter. Previously returned all submissions for a student regardless of query param.
- Security preserved: base queryset already scoped to `student=request.user`, so `?assignment=` cannot leak other students' data.

**`CELERY_TASK_ALWAYS_EAGER = True`** in dev settings:
- Grading pipeline runs synchronously in development — no Celery worker required.

**`seed_demo_data` command**:
- Idempotent (`get_or_create` everywhere)
- Creates: CBSE board, Class 10, Mathematics, Quadratic Equations chapter, demo school, Class 10A, `teacher@demo.openshiksha.org`, `student@demo.openshiksha.org`, 3 LaTeX MCQ/numeric questions, problem set, assignment (due in 7 days)
- Password for both demo accounts: `demo1234`

### Frontend changes

**`QuestionCard.tsx`**:
- Renders `subpart.question_text` with KaTeX (inline `$...$` and block `$$...$$`)
- MCQ: radio group with styled options
- Multi-select: checkbox group
- Numeric: `<input type="number">`
- Fill-blank: `<input type="text">`

**`AssignmentDetailPage.tsx`**:
- Loads assignment detail + existing submission on mount
- Creates submission automatically if none exists
- Debounced auto-save (2s) on each answer change
- Progress bar (answered / total subparts)
- Confirmation dialog before final submit
- Score display after submission (green ≥80%, yellow ≥50%, red <50%)

**`useSubmission.ts`**:
- `useSubmission(assignmentId)` — fetches `GET /api/submissions/?assignment=<id>`
- `useCreateSubmission()` — POST to create blank submission
- `usePatchSubmission(assignmentId)` — PATCH answers/completion/submitted_at

**Teacher UI** (`features/teacher/`):
- `TeacherDashboard` — lists subject rooms, "New Assignment" button
- `CreateAssignmentPage` — cascading form: subject room → problem set (filtered by subject) → due date
- `useSubjectRooms`, `useProblemSets`, `useCreateAssignment` hooks

**`AssignmentList.test.tsx`**:
- All 6 tests now wrapped in `MemoryRouter` — `AssignmentCard` uses `useNavigate()` which requires Router context.

**`ci-cd.yaml`**:
- New `frontend-ci` job: ESLint → tsc → Vitest → build
- `build-publish` now requires `frontend-ci` to pass

## Tests Written

- `AssignmentList.test.tsx` — 6 tests updated, all passing
- `tsc --noEmit` — 0 errors
- `vitest --run` — 11/11 passing
- Django `check` — 0 issues
- `makemigrations --check` — no missing migrations

## Migration Notes

```bash
python manage.py migrate  # applies 0003_add_question_text_and_options_to_questionsubpart
python manage.py seed_demo_data  # one-time demo setup
```

## Next Steps

- Parent monitoring view
- Teacher assignment analytics (per-student submission rates, score distribution)
- Notification system (assignment due, grading complete)
- Mobile-first responsive audit
- Advanced question types (matching, drag-drop)

## PR

openshiksha/openshiksha#64
