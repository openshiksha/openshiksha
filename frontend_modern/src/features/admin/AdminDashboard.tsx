import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  EmptyState,
  Input,
  LoadingSpinner,
  SectionHeading,
  Select,
  Stat,
} from '@/shared/ui';
import { useStandards } from '@/features/teacher/useStandards';
import { useAdminSummary } from './useAdminSummary';
import { useSchoolTeachers } from './useSchoolPeople';
import {
  useClassrooms,
  useCreateClassroom,
  useDeleteClassroom,
  type Classroom,
} from './useClassrooms';

const defaultAcademicYear = (): string => {
  const now = new Date();
  const startYear = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
  return `${startYear}-${String((startYear + 1) % 100).padStart(2, '0')}`;
};

const NewClassroomForm = ({ onDone }: { onDone: () => void }) => {
  const { data: standards } = useStandards();
  const { data: teachers } = useSchoolTeachers();
  const createClassroom = useCreateClassroom();

  const [standard, setStandard] = useState<number | ''>('');
  const [division, setDivision] = useState('');
  const [academicYear, setAcademicYear] = useState(defaultAcademicYear());
  const [classTeacher, setClassTeacher] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (standard === '' || !division.trim() || !academicYear.trim()) {
      setError('Standard, division, and academic year are required.');
      return;
    }
    createClassroom.mutate(
      {
        standard: Number(standard),
        division: division.trim(),
        academic_year: academicYear.trim(),
        class_teacher: classTeacher === '' ? null : Number(classTeacher),
      },
      {
        onSuccess: onDone,
        onError: (err: unknown) => {
          const detail =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            'Could not create classroom. Check for duplicates.';
          setError(detail);
        },
      },
    );
  };

  return (
    <Card>
      <form onSubmit={submit} className="space-y-4">
        <h3 className="font-display font-semibold text-ink-900">New Classroom</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Select
            label="Standard"
            value={standard}
            onChange={(e) => setStandard(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <option value="">Select…</option>
            {standards?.map((s) => (
              <option key={s.id} value={s.id}>
                Grade {s.number}
              </option>
            ))}
          </Select>
          <Input
            label="Division"
            type="text"
            value={division}
            onChange={(e) => setDivision(e.target.value)}
            placeholder="A"
          />
          <Input
            label="Academic Year"
            type="text"
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            placeholder="2026-27"
          />
          <Select
            label="Class Teacher (optional)"
            value={classTeacher}
            onChange={(e) => setClassTeacher(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <option value="">None</option>
            {teachers?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </Select>
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onDone}>
            Cancel
          </Button>
          <Button type="submit" size="sm" disabled={createClassroom.isPending}>
            {createClassroom.isPending ? 'Creating…' : 'Create'}
          </Button>
        </div>
      </form>
    </Card>
  );
};

const ClassroomRow = ({ classroom }: { classroom: Classroom }) => {
  const navigate = useNavigate();
  const deleteClassroom = useDeleteClassroom();

  const onDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (
      window.confirm(
        `Deactivate Grade ${classroom.standard_number}-${classroom.division}? It will be archived, not deleted.`,
      )
    ) {
      deleteClassroom.mutate(classroom.id);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/admin/classrooms/${classroom.id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigate(`/admin/classrooms/${classroom.id}`);
        }
      }}
      className={`os-card p-4 cursor-pointer hover:border-brand-300 hover:bg-brand-50/40 transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 ${
        !classroom.is_active ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="font-semibold text-ink-900">
            Grade {classroom.standard_number}-{classroom.division}
            {!classroom.is_active && (
              <span className="ml-2 text-xs font-medium text-ink-400">(archived)</span>
            )}
          </p>
          <p className="text-sm text-ink-500 mt-0.5">
            {classroom.class_teacher_name ?? 'No class teacher'} · {classroom.academic_year}
          </p>
        </div>
        <div className="text-right shrink-0 flex items-center gap-4">
          <p className="text-sm font-medium text-ink-700">
            {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''}
          </p>
          {classroom.is_active && (
            <button
              type="button"
              onClick={onDelete}
              disabled={deleteClassroom.isPending}
              className="text-xs text-rose-600 hover:text-rose-700 disabled:opacity-50 focus:outline-hidden focus-visible:underline"
            >
              Archive
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export const AdminDashboard = () => {
  const { data: summary, isLoading: summaryLoading } = useAdminSummary();
  const [includeInactive, setIncludeInactive] = useState(false);
  const { data: classrooms, isLoading: classroomsLoading } = useClassrooms(includeInactive);
  const [showForm, setShowForm] = useState(false);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      <SectionHeading
        as="h1"
        title={summary?.school.name ?? 'School Admin'}
        description="Manage classrooms, enrollment, and subject rooms."
        action={
          <Button size="sm" onClick={() => setShowForm((v) => !v)}>
            + New Classroom
          </Button>
        }
      />

      {summaryLoading ? (
        <div className="flex justify-center py-6">
          <LoadingSpinner size="lg" />
        </div>
      ) : summary ? (
        <Card>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
            <Stat label="Classrooms" value={summary.classroom_count} />
            <Stat label="Teachers" value={summary.teacher_count} />
            <Stat label="Students" value={summary.student_count} />
            <Stat label="Subject Rooms" value={summary.active_subject_rooms} />
          </div>
        </Card>
      ) : null}

      {showForm && <NewClassroomForm onDone={() => setShowForm(false)} />}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-display font-semibold text-ink-800">Classrooms</h2>
          <label className="flex items-center gap-2 text-sm text-ink-500 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="w-4 h-4 rounded border-ink-300 text-brand-600 focus:ring-brand-500"
            />
            Show archived
          </label>
        </div>
        {classroomsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !classrooms || classrooms.length === 0 ? (
          <EmptyState
            title="No classrooms yet"
            description="Create one to start onboarding your school."
          />
        ) : (
          <div className="space-y-3">
            {classrooms.map((c) => (
              <ClassroomRow key={c.id} classroom={c} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
