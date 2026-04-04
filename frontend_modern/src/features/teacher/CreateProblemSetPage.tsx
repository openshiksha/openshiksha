import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubjectRooms } from './useSubjectRooms';
import { useChapters } from './useChapters';
import { useQuestionList } from './useQuestionList';
import { useCreateProblemSet } from './useCreateProblemSet';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { Question } from '@/types/index';

const difficultyLabel = (d: number) => '★'.repeat(d) + '☆'.repeat(5 - d);

const QuestionRow = ({
  question,
  selected,
  onToggle,
}: {
  question: Question;
  selected: boolean;
  onToggle: () => void;
}) => {
  const firstSubpart = question.subparts[0];
  const previewText = firstSubpart?.question_text?.replace(/\$[^$]+\$/g, '[math]').slice(0, 80) ?? '(no text)';

  return (
    <label className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
      <input
        type="checkbox"
        checked={selected}
        onChange={onToggle}
        className="mt-0.5 h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
      />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-gray-900 truncate">{previewText}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {question.question_type.replace('_', ' ').toUpperCase()} · {difficultyLabel(question.difficulty)}
        </p>
      </div>
    </label>
  );
};

export const CreateProblemSetPage = () => {
  const navigate = useNavigate();
  const { data: subjectRooms } = useSubjectRooms();

  const [title, setTitle] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | ''>('');
  const [selectedChapterId, setSelectedChapterId] = useState<number | ''>('');
  const [estimatedMinutes, setEstimatedMinutes] = useState<string>('');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState<Set<number>>(new Set());
  const [successId, setSuccessId] = useState<number | null>(null);

  const { data: chapters } = useChapters(
    selectedSubjectId !== '' ? selectedSubjectId : undefined
  );

  const { data: questions, isLoading: questionsLoading } = useQuestionList(
    selectedSubjectId !== '' && selectedChapterId !== ''
      ? { subject: selectedSubjectId as number, chapter: selectedChapterId as number }
      : selectedSubjectId !== ''
      ? { subject: selectedSubjectId as number }
      : {}
  );

  const createProblemSet = useCreateProblemSet();

  const subjects = Array.from(
    new Map(
      subjectRooms?.map((r) => [r.subject, { id: r.subject, name: r.subject_name }]) ?? []
    ).values()
  );

  const toggleQuestion = (id: number) => {
    setSelectedQuestionIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedChapter = chapters?.find((c) => c.id === selectedChapterId);
  const canSubmit =
    title.trim() !== '' &&
    selectedSubjectId !== '' &&
    selectedChapterId !== '' &&
    selectedQuestionIds.size > 0;

  const handleSubmit = async () => {
    if (!canSubmit || !selectedChapter) return;
    const result = await createProblemSet.mutateAsync({
      title: title.trim(),
      standard: selectedChapter.standard,
      subject: selectedSubjectId as number,
      chapter: selectedChapterId as number,
      estimated_minutes: estimatedMinutes ? parseInt(estimatedMinutes, 10) : null,
      question_ids: Array.from(selectedQuestionIds),
    });
    setSuccessId(result.id);
  };

  if (successId !== null) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center">
        <div className="bg-white rounded-xl border border-gray-200 p-10">
          <div className="text-4xl mb-4">✓</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Problem set created!</h2>
          <p className="text-sm text-gray-500 mb-6">
            "{title}" is ready to assign to your students.
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/teacher/assignments/new')}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700"
            >
              Assign it now
            </button>
            <button
              onClick={() => navigate('/teacher')}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50"
            >
              Back to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Build Problem Set</h1>
          <p className="text-sm text-gray-500 mt-1">Group questions into an assignable set.</p>
        </div>
        <button
          onClick={() => navigate('/teacher')}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Back
        </button>
      </div>

      {/* Details card */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <h2 className="font-semibold text-gray-800">Details</h2>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. Quadratic Equations Practice Set 1"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Subject</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={selectedSubjectId}
              onChange={(e) => {
                setSelectedSubjectId(e.target.value ? Number(e.target.value) : '');
                setSelectedChapterId('');
                setSelectedQuestionIds(new Set());
              }}
            >
              <option value="">Select subject...</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Chapter</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              value={selectedChapterId}
              onChange={(e) => {
                setSelectedChapterId(e.target.value ? Number(e.target.value) : '');
                setSelectedQuestionIds(new Set());
              }}
              disabled={!selectedSubjectId || !chapters}
            >
              <option value="">Select chapter...</option>
              {chapters?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (Std {c.standard_number})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="w-40">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Estimated time (minutes, optional)
          </label>
          <input
            type="number"
            min="1"
            max="180"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. 30"
            value={estimatedMinutes}
            onChange={(e) => setEstimatedMinutes(e.target.value)}
          />
        </div>
      </div>

      {/* Questions picker */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Select Questions</h2>
          {selectedQuestionIds.size > 0 && (
            <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
              {selectedQuestionIds.size} selected
            </span>
          )}
        </div>

        <div className="p-3">
          {!selectedSubjectId ? (
            <p className="text-sm text-gray-400 text-center py-6">Select a subject to browse questions.</p>
          ) : questionsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : !questions || questions.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">
              No questions found for this subject.{' '}
              <button
                onClick={() => navigate('/teacher/questions/new')}
                className="text-indigo-600 hover:underline"
              >
                Author one?
              </button>
            </p>
          ) : (
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {questions.map((q) => (
                <QuestionRow
                  key={q.id}
                  question={q}
                  selected={selectedQuestionIds.has(q.id)}
                  onToggle={() => toggleQuestion(q.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Submit */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={!canSubmit || createProblemSet.isPending}
          className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {createProblemSet.isPending && <LoadingSpinner size="sm" />}
          Create Problem Set
        </button>
        {!canSubmit && (
          <p className="text-xs text-gray-400">Fill in all details and select at least one question.</p>
        )}
        {createProblemSet.isError && (
          <p className="text-xs text-red-500">Failed to create. Please try again.</p>
        )}
      </div>
    </div>
  );
};
