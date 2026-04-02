import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useProblemSets } from './useProblemSets';
import { useCreateAssignment } from './useCreateAssignment';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';

export const CreateAssignmentPage = () => {
  const navigate = useNavigate();

  const [subjectRoomId, setSubjectRoomId] = useState<number | null>(null);
  const [problemSetId, setProblemSetId] = useState<number | null>(null);
  const [dueDate, setDueDate] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { data: subjectRooms, isLoading: roomsLoading } = useSubjectRooms();

  const selectedRoom = subjectRooms?.find((r) => r.id === subjectRoomId) ?? null;
  const subjectId = selectedRoom?.subject ?? null;

  const { data: problemSets, isLoading: setsLoading } = useProblemSets(subjectId);

  const createAssignment = useCreateAssignment();

  const isFormValid = subjectRoomId !== null && problemSetId !== null && dueDate !== '';

  const handleRoomChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSubjectRoomId(Number(e.target.value) || null);
    setProblemSetId(null);
    setErrorMessage('');
    setSuccessMessage('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    createAssignment.mutate(
      {
        subject_room: subjectRoomId!,
        problem_set_id: problemSetId!,
        due_at: new Date(dueDate).toISOString(),
      },
      {
        onSuccess: () => {
          setSuccessMessage('Assignment created! Students can now see it in their dashboard.');
          setSubjectRoomId(null);
          setProblemSetId(null);
          setDueDate('');
        },
        onError: () => {
          setErrorMessage('Failed to create assignment. Please try again.');
        },
      }
    );
  };

  const minDate = new Date();
  minDate.setDate(minDate.getDate() + 1);
  const minDateStr = minDate.toISOString().split('T')[0];

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <div className="mb-6">
        <button
          onClick={() => navigate('/teacher')}
          className="text-sm text-indigo-600 hover:underline mb-3 flex items-center gap-1"
        >
          <span>&#8592;</span> Back to dashboard
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Create Assignment</h1>
        <p className="text-sm text-gray-500 mt-1">
          Assign a problem set to one of your subject rooms.
        </p>
      </div>

      {successMessage && (
        <div className="mb-6 rounded-xl bg-green-50 border border-green-200 p-4">
          <p className="text-sm text-green-800">{successMessage}</p>
          <button
            onClick={() => navigate('/teacher')}
            className="mt-2 text-sm text-green-700 font-medium hover:underline"
          >
            Go to dashboard
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mb-6 rounded-xl bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-800">{errorMessage}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-2xl border border-gray-200 p-6">
        {/* Subject Room */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Subject Room
          </label>
          {roomsLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <LoadingSpinner size="sm" /> Loading rooms...
            </div>
          ) : (
            <select
              value={subjectRoomId ?? ''}
              onChange={handleRoomChange}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">Select a subject room...</option>
              {(subjectRooms ?? []).map((room) => (
                <option key={room.id} value={room.id}>
                  {room.subject_name} — {room.classroom_display} ({room.student_count} students)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Problem Set */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Problem Set
          </label>
          {subjectRoomId === null ? (
            <p className="text-sm text-gray-400">Select a subject room first.</p>
          ) : setsLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <LoadingSpinner size="sm" /> Loading problem sets...
            </div>
          ) : !problemSets || problemSets.length === 0 ? (
            <p className="text-sm text-gray-400">
              No problem sets found for this subject.
            </p>
          ) : (
            <select
              value={problemSetId ?? ''}
              onChange={(e) => setProblemSetId(Number(e.target.value) || null)}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white"
            >
              <option value="">Select a problem set...</option>
              {problemSets.map((ps) => (
                <option key={ps.id} value={ps.id}>
                  {ps.title} ({ps.question_count} questions
                  {ps.estimated_minutes ? `, ~${ps.estimated_minutes} min` : ''})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Due Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Due Date
          </label>
          <input
            type="date"
            value={dueDate}
            min={minDateStr}
            onChange={(e) => setDueDate(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={!isFormValid || createAssignment.isPending}
          className="w-full bg-indigo-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {createAssignment.isPending ? 'Creating...' : 'Create Assignment'}
        </button>
      </form>
    </div>
  );
};
