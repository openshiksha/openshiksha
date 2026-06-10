import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useTeacherAssignments } from './useTeacherAssignments';
import { useProblemSets } from './useProblemSets';
import { ClassHealthPanel } from './ClassHealthPanel';
import { WeeklyReportPanel } from './WeeklyReportPanel';
import { InterventionsPanel } from './InterventionsPanel';
import { MisconceptionClustersPanel } from './MisconceptionClustersPanel';
import { QuestionQualityPanel } from './QuestionQualityPanel';
import { ClassroomCodeWidget } from './ClassroomCodeWidget';
import { NeedsAttentionPanel } from './NeedsAttentionPanel';
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

/**
 * The four analytics panels used to render eagerly inside every subject-room
 * card — four data-fetching panels per room, stacked open, on first paint.
 * They now live behind one disclosure and only mount (and fetch) when a teacher
 * actually opens them. Default state of a room card is lean: identity + assign.
 */
const RoomInsights = ({ subjectRoomId }: { subjectRoomId: number }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-4 border-t border-ink-100 pt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center gap-1.5 text-left text-xs font-semibold text-ink-600 transition-colors hover:text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span className="text-ink-400">{open ? '▾' : '▸'}</span>
        {open ? 'Hide class insights' : 'View class insights'}
      </button>
      {open && (
        <div className="mt-3 space-y-3">
          <ClassHealthPanel subjectRoomId={subjectRoomId} />
          <WeeklyReportPanel subjectRoomId={subjectRoomId} />
          <InterventionsPanel subjectRoomId={subjectRoomId} />
          <MisconceptionClustersPanel subjectRoomId={subjectRoomId} />
          <QuestionQualityPanel subjectRoomId={subjectRoomId} />
        </div>
      )}
    </div>
  );
};

export const TeacherDashboard = () => {
  const navigate = useNavigate();
  const { data: subjectRooms, isLoading: roomsLoading } = useSubjectRooms();
  const { data: assignments, isLoading: assignmentsLoading } = useTeacherAssignments();
  const { data: problemSets, isLoading: setsLoading } = useProblemSets();

  const totalStudents = (subjectRooms ?? []).reduce((sum, r) => sum + r.student_count, 0);
  const openCount = (assignments ?? []).filter((a) => !isOverdue(a.due_at)).length;

  // The join code is per *classroom*, but a teacher can run several subject
  // rooms inside the same classroom. Dedupe so we show one code per classroom
  // instead of a duplicate widget under every subject room.
  const uniqueClassrooms = Array.from(
    new Map(
      (subjectRooms ?? []).map((r) => [r.classroom, { id: r.classroom, name: r.classroom_display }]),
    ).values(),
  );

  return (
    <div className="mx-auto max-w-3xl space-y-8 px-4 py-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <h1 className="font-display text-3xl font-semibold text-ink-900">Teacher dashboard</h1>
          <p className="mt-1 text-sm text-ink-500">
            Your rooms, problem sets, and assignments in one place.
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/questions/new')}>
            + Question
          </Button>
          <Button variant="ghost" size="sm" onClick={() => navigate('/teacher/problem-sets/new')}>
            + Problem set
          </Button>
          <Button size="sm" onClick={() => navigate('/teacher/assignments/new')}>
            + Assignment
          </Button>
        </div>
      </div>

      {/* Needs attention — surfaces overdue / ungraded / low-completion before the room cards */}
      <NeedsAttentionPanel assignments={assignments} />

      {/* Headline stats */}
      {(subjectRooms?.length ?? 0) > 0 && (
        <Card className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <Stat label="Subject rooms" value={subjectRooms?.length ?? 0} />
          <Stat label="Students" value={totalStudents} />
          <Stat label="Problem sets" value={problemSets?.length ?? 0} />
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
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-ink-900">{room.subject_name}</p>
                    <p className="text-sm text-ink-500">{room.classroom_display}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <span className="text-sm text-ink-500">
                      {room.student_count} student{room.student_count !== 1 ? 's' : ''}
                    </span>
                    <Button
                      size="sm"
                      onClick={() => navigate(`/teacher/assignments/new?room=${room.id}`)}
                    >
                      Assign
                    </Button>
                  </div>
                </div>
                <RoomInsights subjectRoomId={room.id} />
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Problem sets — with student preview */}
      {(subjectRooms?.length ?? 0) > 0 && (
        <section className="space-y-3">
          <SectionHeading
            title="Problem sets"
            as="h2"
            action={
              <button
                type="button"
                onClick={() => navigate('/teacher/problem-sets/new')}
                className="text-sm font-medium text-brand-700 hover:text-brand-800"
              >
                + New set
              </button>
            }
          />
          {setsLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : !problemSets || problemSets.length === 0 ? (
            <EmptyState
              title="No problem sets yet"
              description="Build a set of questions you can assign to any of your rooms."
              action={
                <Button onClick={() => navigate('/teacher/problem-sets/new')}>
                  Build a problem set
                </Button>
              }
            />
          ) : (
            <div className="space-y-2">
              {problemSets.map((ps) => (
                <Card key={ps.id} padded={false} className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-ink-900">{ps.title}</p>
                      <p className="mt-0.5 text-xs text-ink-500">
                        {ps.subject_name} · {ps.chapter_name} · {ps.question_count} question
                        {ps.question_count !== 1 ? 's' : ''}
                        {ps.estimated_minutes != null && ` · ~${ps.estimated_minutes} min`}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/teacher/problem-sets/${ps.id}/preview`)}
                      >
                        Preview as student
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => navigate(`/teacher/assignments/new?problemSet=${ps.id}`)}
                      >
                        Assign
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Classroom join codes — one per classroom (deduped) */}
      {uniqueClassrooms.length > 0 && (
        <section className="space-y-3">
          <SectionHeading
            title="Class join codes"
            as="h2"
            description="Share a code so students can join the classroom themselves."
          />
          <div className="space-y-3">
            {uniqueClassrooms.map((c) => (
              <Card key={c.id} padded={false} className="p-4">
                <p className="font-semibold text-ink-900">{c.name}</p>
                <ClassroomCodeWidget classroomId={c.id} classroomName={c.name} />
              </Card>
            ))}
          </div>
        </section>
      )}

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
