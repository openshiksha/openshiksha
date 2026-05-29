import { useMemo, useState } from 'react';
import type { SchoolPerson } from './useSchoolPeople';
import type { EnrollmentResult } from './useClassrooms';

interface EnrollStudentsModalProps {
  title: string;
  students: SchoolPerson[];
  isPending: boolean;
  onAction: (studentIds: number[], action: 'enroll' | 'unenroll') => Promise<EnrollmentResult>;
  onClose: () => void;
}

export const EnrollStudentsModal = ({
  title,
  students,
  isPending,
  onAction,
  onClose,
}: EnrollStudentsModalProps) => {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<{ action: string; count: number; invalid: number } | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return students;
    return students.filter(
      (s) => s.full_name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q)
    );
  }, [students, search]);

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const run = async (action: 'enroll' | 'unenroll') => {
    if (selected.size === 0) return;
    setError(null);
    try {
      const res = await onAction(Array.from(selected), action);
      const changed = action === 'enroll' ? res.enrolled ?? [] : res.unenrolled ?? [];
      setResult({ action, count: changed.length, invalid: res.invalid_ids.length });
      setSelected(new Set());
    } catch {
      setError('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-5 py-3 border-b border-gray-100">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search students by name or email…"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-gray-400 py-6 text-center">No students found.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {filtered.map((s) => (
                <li key={s.id}>
                  <label className="flex items-center gap-3 py-2.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selected.has(s.id)}
                      onChange={() => toggle(s.id)}
                      className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="min-w-0">
                      <span className="block text-sm font-medium text-gray-900 truncate">
                        {s.full_name}
                      </span>
                      <span className="block text-xs text-gray-500 truncate">{s.email}</span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>

        {(result || error) && (
          <div className="px-5 py-2 text-sm border-t border-gray-100">
            {error ? (
              <span className="text-red-600">{error}</span>
            ) : (
              <span className="text-gray-600">
                {result!.count} student{result!.count !== 1 ? 's' : ''} {result!.action}ed
                {result!.invalid > 0 && ` · ${result!.invalid} skipped (invalid)`}
              </span>
            )}
          </div>
        )}

        <div className="flex items-center justify-end gap-2 px-5 py-4 border-t border-gray-100">
          <span className="text-xs text-gray-500 mr-auto">{selected.size} selected</span>
          <button
            onClick={() => run('unenroll')}
            disabled={isPending || selected.size === 0}
            className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            Remove
          </button>
          <button
            onClick={() => run('enroll')}
            disabled={isPending || selected.size === 0}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            Enroll
          </button>
        </div>
      </div>
    </div>
  );
};
