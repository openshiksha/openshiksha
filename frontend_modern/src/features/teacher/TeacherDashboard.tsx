import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';

export const TeacherDashboard = () => {
  const navigate = useNavigate();
  const { data: subjectRooms, isLoading } = useSubjectRooms();

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Teacher Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your subject rooms and assignments.</p>
        </div>
        <button
          onClick={() => navigate('/teacher/assignments/new')}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          + New Assignment
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : !subjectRooms || subjectRooms.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No subject rooms yet.</p>
          <p className="text-sm mt-1">Ask an admin to assign you to a classroom.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {subjectRooms.map((room) => (
            <div
              key={room.id}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
