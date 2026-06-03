import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useTeacherAssignments } from './useTeacherAssignments';
import { ClassHealthPanel } from './ClassHealthPanel';
import { WeeklyReportPanel } from './WeeklyReportPanel';
import { InterventionsPanel } from './InterventionsPanel';
import { ClassroomCodeWidget } from './ClassroomCodeWidget';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import { Button, Card, EmptyState, SectionHeading, Stat } from '@/shared/ui';
import type { Assignment } from '@/types/index';

const isOverdue = (dueAt: string) => new Date(dueAt) < new Date();

const AssignmentRow = ({ assignment }: { assignment: Assignment }) => {
  const navigate = useNavigate();
  const { submission_count, student_count, average_score, due_at, problem_set, subject_room_display } = assignment;
  const pct = student_count > 0 ? (submission_count / student_count) * 100 : 0;
  const overdue = isOverdue(due_at);
  const dueDate = new Date(due_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

  return (
    <button
      type="button"
      onClick={() => navigate(`/teacher/assignments/${assignment.id}`)}
      className="os-card w-full p-4 text-left transition-colors hover:border-brand-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate font-semibold text-ink-900">{problem_set.title}</p>
          <p className="mt-0.5 text-sm text-ink-500">{subject_room_display}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className={`text-xs font-medium ${overdue ? 'text-rose-600' : 'text-ink-500'}`}>
            {overdue ? 'Overdue' : `Due ${dueDate}`}
          </p>
          <p className="mt-0.5 text-sm font-medium text-ink-700">
            {submission_count}/{student_count} submitted
          </p>
          {average_score !== null && (
            <p className="text-xs text-ink-500">Avg: {Math.round(average_score * 100)}%</p>
          )}
        </div>
      </div>
      <div className="mt-3">
        <div className="h-1.5 overflow-hidden rounded-full bg-ink-100">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </button>
  );
};

export const TeacherDashboard = () => {
  const navigate = useNavigate();
  const { data: subjectRooms, isLoading: roomsLoading } = useSubjectRooms();
  const { data: assignments, isLoading: assignmentsLoading } = useTeacherAssignments();

  const totalStudents = (subjectRooms ?? []).reduce((sum, r) => sum + r.student_count, 0);
  const openCount = (assignments ?? []).filter((a) => !isOverdue(a.due_at)).length;

  return (
    <div className="mx-auto max-w-2xl space-y-8 px-4 py-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-3xl font-semibold text-ink-900">Teacher dashboard</h1>
          <p className="mt-1 text-sm text-ink-500">
            Manage your subject rooms and assignments.
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/questions/new')}>
            + New question
          </Button>
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/problem-sets/new')}>
            + Problem set
          </Button>
          <Button size="sm" onClick={() => navigate('/teacher/assignments/new')}>
            + New assignment
          </Button>
        </div>
      </div>

      {/* Headline stats */}
      {(subjectRooms?.length ?? 0) > 0 && (
        <Card className="grid grid-cols-2 gap-6 sm:grid-cols-3">
          <Stat label="Subject rooms" value={subjectRooms?.length ?? 0} />
          <Stat label="Students" value={totalStudents} />
          <Stat label="Open assignments" value={openCount} />
        </Card>
      )}

      {/* Subject Rooms */}
      <section className="space-y-3">
        <SectionHeading title="Subject rooms" as="h2" />
        {roomsLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !subjectRooms || subjectRooms.length === 0 ? (
          <EmptyState
            title="No subject rooms yet"
            description="Ask an admin to assign you to a classroom."
          />
        ) : (
          <div className="space-y-3">
            {subjectRooms.map((room) => (
              <Card key={room.id} padded={false} className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-ink-900">{room.subject_name}</p>
                    <p className="text-sm text-ink-500">{room.classroom_display}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-ink-700">
                      {room.student_count} student{room.student_count !== 1 ? 's' : ''}
                    </p>
                    <button
                      onClick={() => navigate('/teacher/assignments/new')}
                      className="mt-0.5 text-xs font-semibold text-brand-700 hover:text-brand-800"
                    >
                      Assign problem set
                    </button>
                  </div>
                </div>
                <ClassHealthPanel subjectRoomId={room.id} />
                <WeeklyReportPanel subjectRoomId={room.id} />
                <InterventionsPanel subjectRoomId={room.id} />
                <ClassroomCodeWidget
                  classroomId={room.classroom}
                  classroomName={room.classroom_display}
                />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Assignments */}
      <section className="space-y-3">
        <SectionHeading title="Assignments" as="h2" />
        {assignmentsLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !assignments || assignments.length === 0 ? (
          <EmptyState
            title="No assignments yet"
            description="Create your first assignment to start tracking submissions."
            action={
              <Button onClick={() => navigate('/teacher/assignments/new')}>
                Create assignment
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {assignments.map((a) => (
              <AssignmentRow key={a.id} assignment={a} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
