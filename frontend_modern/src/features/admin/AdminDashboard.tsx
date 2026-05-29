import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
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
  // Indian academic year runs ~Apr–Mar; before April belongs to the prior year's intake.
  const startYear = now.getMonth() >= 3 ? now.getFullYear() : now.getFullYear() - 1;
  return `${startYear}-${String((startYear + 1) % 100).padStart(2, '0')}`;
};

const SummaryCard = ({ label, value }: { label: string; value: number }) => (
  <div className="bg-white rounded-xl border border-gray-200 p-5">
    <p className="text-2xl font-bold text-gray-900">{value}</p>
    <p className="text-sm text-gray-500 mt-1">{label}</p>
  </div>
);

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
      }
    );
  };

  return (
    <form onSubmit={submit} className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <h3 className="font-semibold text-gray-900">New Classroom</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Standard</span>
          <select
            value={standard}
            onChange={(e) => setStandard(e.target.value === '' ? '' : Number(e.target.value))}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select…</option>
            {standards?.map((s) => (
              <option key={s.id} value={s.id}>
                Grade {s.number}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Division</span>
          <input
            type="text"
            value={division}
            onChange={(e) => setDivision(e.target.value)}
            placeholder="A"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Academic Year</span>
          <input
            type="text"
            value={academicYear}
            onChange={(e) => setAcademicYear(e.target.value)}
            placeholder="2026-27"
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Class Teacher (optional)</span>
          <select
            value={classTeacher}
            onChange={(e) => setClassTeacher(e.target.value === '' ? '' : Number(e.target.value))}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">None</option>
            {teachers?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onDone}
          className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={createClassroom.isPending}
          className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {createClassroom.isPending ? 'Creating…' : 'Create'}
        </button>
      </div>
    </form>
  );
};

const ClassroomRow = ({ classroom }: { classroom: Classroom }) => {
  const navigate = useNavigate();
  const deleteClassroom = useDeleteClassroom();

  const onDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (
      window.confirm(
        `Deactivate Grade ${classroom.standard_number}-${classroom.division}? It will be archived, not deleted.`
      )
    ) {
      deleteClassroom.mutate(classroom.id);
    }
  };

  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:border-indigo-300 transition-colors ${
        !classroom.is_active ? 'opacity-60' : ''
      }`}
      onClick={() => navigate(`/admin/classrooms/${classroom.id}`)}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900">
            Grade {classroom.standard_number}-{classroom.division}
            {!classroom.is_active && (
              <span className="ml-2 text-xs font-medium text-gray-400">(archived)</span>
            )}
          </p>
          <p className="text-sm text-gray-500 mt-0.5">
            {classroom.class_teacher_name ?? 'No class teacher'} · {classroom.academic_year}
          </p>
        </div>
        <div className="text-right shrink-0 flex items-center gap-4">
          <p className="text-sm font-medium text-gray-700">
            {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''}
          </p>
          {classroom.is_active && (
            <button
              onClick={onDelete}
              disabled={deleteClassroom.isPending}
              className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {summary?.school.name ?? 'School Admin'}
          </h1>
          <p className="text-sm text-gray-500 mt-1">Manage classrooms, enrollment, and subject rooms.</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          + New Classroom
        </button>
      </div>

      {summaryLoading ? (
        <div className="flex justify-center py-6">
          <LoadingSpinner size="lg" />
        </div>
      ) : summary ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <SummaryCard label="Classrooms" value={summary.classroom_count} />
          <SummaryCard label="Teachers" value={summary.teacher_count} />
          <SummaryCard label="Students" value={summary.student_count} />
          <SummaryCard label="Subject Rooms" value={summary.active_subject_rooms} />
        </div>
      ) : null}

      {showForm && <NewClassroomForm onDone={() => setShowForm(false)} />}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800">Classrooms</h2>
          <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            Show archived
          </label>
        </div>
        {classroomsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !classrooms || classrooms.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-white rounded-xl border border-gray-200">
            <p className="text-sm">No classrooms yet. Create one to start onboarding your school.</p>
          </div>
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
