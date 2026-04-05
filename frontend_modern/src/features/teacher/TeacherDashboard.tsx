import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useTeacherAssignments } from './useTeacherAssignments';
import { ClassHealthPanel } from './ClassHealthPanel';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { Assignment } from '@/types/index';

const isOverdue = (dueAt: string) => new Date(dueAt) < new Date();

const AssignmentRow = ({ assignment }: { assignment: Assignment }) => {
  const navigate = useNavigate();
  const { submission_count, student_count, average_score, due_at, problem_set, subject_room_display } = assignment;
  const pct = student_count > 0 ? (submission_count / student_count) * 100 : 0;
  const overdue = isOverdue(due_at);
  const dueDate = new Date(due_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:border-indigo-300 transition-colors"
      onClick={() => navigate(`/teacher/assignments/${assignment.id}`)}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 truncate">{problem_set.title}</p>
          <p className="text-sm text-gray-500 mt-0.5">{subject_room_display}</p>
        </div>
        <div className="text-right shrink-0">
          <p className={`text-xs font-medium ${overdue ? 'text-red-500' : 'text-gray-500'}`}>
            {overdue ? 'Overdue' : `Due ${dueDate}`}
          </p>
          <p className="text-sm font-medium text-gray-700 mt-0.5">
            {submission_count}/{student_count} submitted
          </p>
          {average_score !== null && (
            <p className="text-xs text-gray-500">Avg: {Math.round(average_score * 100)}%</p>
          )}
        </div>
      </div>
      <div className="mt-3">
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export const TeacherDashboard = () => {
  const navigate = useNavigate();
  const { data: subjectRooms, isLoading: roomsLoading } = useSubjectRooms();
  const { data: assignments, isLoading: assignmentsLoading } = useTeacherAssignments();

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your subject rooms and assignments.</p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          <button
            onClick={() => navigate('/teacher/questions/new')}
            className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            + New Question
          </button>
          <button
            onClick={() => navigate('/teacher/problem-sets/new')}
            className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            + Problem Set
          </button>
          <button
            onClick={() => navigate('/teacher/assignments/new')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            + New Assignment
          </button>
        </div>
      </div>

      {/* Subject Rooms */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Subject Rooms</h2>
        {roomsLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !subjectRooms || subjectRooms.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-white rounded-xl border border-gray-200">
            <p className="text-sm">No subject rooms yet. Ask an admin to assign you to a classroom.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {subjectRooms.map((room) => (
              <div key={room.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{room.subject_name}</p>
                    <p className="text-sm text-gray-500">{room.classroom_display}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700">
                      {room.student_count} student{room.student_count !== 1 ? 's' : ''}
                    </p>
                    <button
                      onClick={() => navigate('/teacher/assignments/new')}
                      className="text-xs text-indigo-600 hover:underline mt-0.5"
                    >
                      Assign problem set
                    </button>
                  </div>
                </div>
                <ClassHealthPanel subjectRoomId={room.id} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Assignments */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Assignments</h2>
        {assignmentsLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : !assignments || assignments.length === 0 ? (
          <div className="text-center py-8 text-gray-400 bg-white rounded-xl border border-gray-200">
            <p className="text-sm">No assignments yet.</p>
            <button
              onClick={() => navigate('/teacher/assignments/new')}
              className="mt-2 text-sm text-indigo-600 hover:underline"
            >
              Create your first assignment
            </button>
          </div>
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
