import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { useSubjects } from '@/features/teacher/useSubjects';
import { useClassroom, useClassroomEnrollment } from './useClassrooms';
import { useSchoolStudents, useSchoolTeachers } from './useSchoolPeople';
import {
  useAdminSubjectRooms,
  useCreateSubjectRoom,
  useSubjectRoomEnrollment,
  type AdminSubjectRoom,
} from './useAdminSubjectRooms';
import { EnrollStudentsModal } from './EnrollStudentsModal';

const NewSubjectRoomForm = ({
  classroomId,
  onDone,
}: {
  classroomId: number;
  onDone: () => void;
}) => {
  const { data: subjects } = useSubjects();
  const { data: teachers } = useSchoolTeachers();
  const createRoom = useCreateSubjectRoom();
  const [subject, setSubject] = useState<number | ''>('');
  const [teacher, setTeacher] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (subject === '' || teacher === '') {
      setError('Subject and teacher are required.');
      return;
    }
    createRoom.mutate(
      { classroom: classroomId, subject: Number(subject), teacher: Number(teacher) },
      {
        onSuccess: onDone,
        onError: (err: unknown) => {
          const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
          const msg =
            (data?.detail as string) ||
            (Array.isArray(data?.non_field_errors)
              ? (data!.non_field_errors as string[])[0]
              : null) ||
            'Could not create subject room. A room for this subject may already exist.';
          setError(msg);
        },
      }
    );
  };

  return (
    <form onSubmit={submit} className="bg-gray-50 rounded-xl border border-gray-200 p-4 space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Subject</span>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value === '' ? '' : Number(e.target.value))}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select subject…</option>
            {subjects?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Teacher</span>
          <select
            value={teacher}
            onChange={(e) => setTeacher(e.target.value === '' ? '' : Number(e.target.value))}
            className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">Select teacher…</option>
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
          className="px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-white transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={createRoom.isPending}
          className="px-3 py-1.5 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {createRoom.isPending ? 'Creating…' : 'Create Subject Room'}
        </button>
      </div>
    </form>
  );
};

export const ClassroomManagePage = () => {
  const { id } = useParams<{ id: string }>();
  const classroomId = Number(id);
  const navigate = useNavigate();

  const { data: classroom, isLoading } = useClassroom(classroomId);
  const { data: allRooms, isLoading: roomsLoading } = useAdminSubjectRooms();
  const { data: students } = useSchoolStudents();
  const classroomEnrollment = useClassroomEnrollment();
  const subjectRoomEnrollment = useSubjectRoomEnrollment();

  const [showRoster, setShowRoster] = useState(false);
  const [showNewRoom, setShowNewRoom] = useState(false);
  const [enrollingRoom, setEnrollingRoom] = useState<AdminSubjectRoom | null>(null);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!classroom) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-gray-500">
        <p>Classroom not found.</p>
        <button onClick={() => navigate('/admin')} className="mt-3 text-sm text-indigo-600 hover:underline">
          Back to dashboard
        </button>
      </div>
    );
  }

  const rooms = (allRooms ?? []).filter((r) => r.classroom === classroomId);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      <button onClick={() => navigate('/admin')} className="text-sm text-indigo-600 hover:underline">
        ← Back to dashboard
      </button>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Grade {classroom.standard_number}-{classroom.division}
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {classroom.class_teacher_name ?? 'No class teacher'} · {classroom.academic_year} ·{' '}
          {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''}
        </p>
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800">Roster</h2>
          <button
            onClick={() => setShowRoster(true)}
            className="text-sm text-indigo-600 hover:underline"
          >
            Manage students
          </button>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 text-sm text-gray-600">
          {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''} enrolled in this
          classroom. Use “Manage students” to enroll or remove students.
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800">Subject Rooms</h2>
          <button
            onClick={() => setShowNewRoom((v) => !v)}
            className="text-sm text-indigo-600 hover:underline"
          >
            + Add subject room
          </button>
        </div>

        {showNewRoom && (
          <div className="mb-3">
            <NewSubjectRoomForm classroomId={classroomId} onDone={() => setShowNewRoom(false)} />
          </div>
        )}

        {roomsLoading ? (
          <div className="flex justify-center py-6">
            <LoadingSpinner size="lg" />
          </div>
        ) : rooms.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-white rounded-xl border border-gray-200">
            <p className="text-sm">No subject rooms yet. Add one to assign a teacher and students.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {rooms.map((room) => (
              <div
                key={room.id}
                className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between"
              >
                <div>
                  <p className="font-semibold text-gray-900">{room.subject_name}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{room.teacher_name}</p>
                </div>
                <div className="text-right flex items-center gap-4">
                  <p className="text-sm font-medium text-gray-700">
                    {room.student_count} student{room.student_count !== 1 ? 's' : ''}
                  </p>
                  <button
                    onClick={() => setEnrollingRoom(room)}
                    className="text-xs text-indigo-600 hover:underline"
                  >
                    Manage students
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {showRoster && (
        <EnrollStudentsModal
          title={`Roster — Grade ${classroom.standard_number}-${classroom.division}`}
          students={students ?? []}
          isPending={classroomEnrollment.isPending}
          onAction={(studentIds, action) =>
            classroomEnrollment.mutateAsync({ id: classroomId, studentIds, action })
          }
          onClose={() => setShowRoster(false)}
        />
      )}

      {enrollingRoom && (
        <EnrollStudentsModal
          title={`${enrollingRoom.subject_name} — students`}
          students={students ?? []}
          isPending={subjectRoomEnrollment.isPending}
          onAction={(studentIds, action) =>
            subjectRoomEnrollment.mutateAsync({ id: enrollingRoom.id, studentIds, action })
          }
          onClose={() => setEnrollingRoom(null)}
        />
      )}
    </div>
  );
};
