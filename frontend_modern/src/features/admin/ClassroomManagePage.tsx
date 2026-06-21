import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card, EmptyState, LoadingSpinner, Select } from '@/shared/ui';
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
      },
    );
  };

  return (
    <form onSubmit={submit} className="rounded-xl border border-ink-200 bg-paper p-4 space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Select
          label="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value === '' ? '' : Number(e.target.value))}
        >
          <option value="">Select subject…</option>
          {subjects?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select
          label="Teacher"
          value={teacher}
          onChange={(e) => setTeacher(e.target.value === '' ? '' : Number(e.target.value))}
        >
          <option value="">Select teacher…</option>
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
        <Button type="submit" size="sm" disabled={createRoom.isPending}>
          {createRoom.isPending ? 'Creating…' : 'Create Subject Room'}
        </Button>
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
      <div className="max-w-2xl mx-auto px-4 py-16">
        <EmptyState
          title="Classroom not found"
          action={
            <Button variant="ghost" size="sm" onClick={() => navigate('/admin')}>
              Back to dashboard
            </Button>
          }
        />
      </div>
    );
  }

  const rooms = (allRooms ?? []).filter((r) => r.classroom === classroomId);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      <button
        type="button"
        onClick={() => navigate('/admin')}
        className="text-sm text-brand-700 font-medium hover:underline focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        ← Back to dashboard
      </button>

      <div>
        <h1 className="text-2xl font-display font-semibold text-ink-900">
          Grade {classroom.standard_number}-{classroom.division}
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          {classroom.class_teacher_name ?? 'No class teacher'} · {classroom.academic_year} ·{' '}
          {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''}
        </p>
      </div>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-display font-semibold text-ink-800">Roster</h2>
          <button
            type="button"
            onClick={() => setShowRoster(true)}
            className="text-sm text-brand-700 font-medium hover:underline focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
          >
            Manage students
          </button>
        </div>
        <Card className="text-sm text-ink-700 p-5">
          {classroom.student_count} student{classroom.student_count !== 1 ? 's' : ''} enrolled in this
          classroom. Use “Manage students” to enroll or remove students.
        </Card>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-display font-semibold text-ink-800">Subject Rooms</h2>
          <button
            type="button"
            onClick={() => setShowNewRoom((v) => !v)}
            className="text-sm text-brand-700 font-medium hover:underline focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
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
          <EmptyState
            title="No subject rooms yet"
            description="Add one to assign a teacher and students."
          />
        ) : (
          <div className="space-y-3">
            {rooms.map((room) => (
              <Card key={room.id} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-ink-900">{room.subject_name}</p>
                  <p className="text-sm text-ink-500 mt-0.5">{room.teacher_name}</p>
                </div>
                <div className="text-right flex items-center gap-4">
                  <p className="text-sm font-medium text-ink-700">
                    {room.student_count} student{room.student_count !== 1 ? 's' : ''}
                  </p>
                  <button
                    type="button"
                    onClick={() => setEnrollingRoom(room)}
                    className="text-xs text-brand-700 font-medium hover:underline focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
                  >
                    Manage students
                  </button>
                </div>
              </Card>
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
