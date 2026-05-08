import { useState } from 'react';
import { useChildren } from './useChildren';
import { useChildProficiency } from './useChildProficiency';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { User, StudentProficiency } from '@/types/index';

interface SubjectGroup {
  subjectName: string;
  classroomDisplay: string;
  records: StudentProficiency[];
}

const groupBySubject = (records: StudentProficiency[]): SubjectGroup[] => {
  const map = new Map<string, SubjectGroup>();
  for (const r of records) {
    const key = `${r.subject_name}|${r.classroom_display}`;
    if (!map.has(key)) {
      map.set(key, { subjectName: r.subject_name, classroomDisplay: r.classroom_display, records: [] });
    }
    map.get(key)!.records.push(r);
  }
  return Array.from(map.values());
};

const ProficiencyBar = ({ record }: { record: StudentProficiency }) => {
  const pct = Math.round(record.score * 100);
  const barColor = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-400' : 'bg-red-400';

  return (
    <div className="py-2.5">
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="text-sm font-medium text-gray-800 truncate">{record.tag_name}</span>
        <span className="text-sm font-semibold text-gray-700 shrink-0">{pct}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-1">
        {record.tick_count} question{record.tick_count !== 1 ? 's' : ''} practised
      </p>
    </div>
  );
};

const ChildView = ({ child }: { child: User }) => {
  const { data: records, isLoading } = useChildProficiency(child.id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (!records || records.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
        <p className="text-gray-500 font-medium">No progress yet</p>
        <p className="text-sm text-gray-400 mt-1">
          {child.first_name || child.username} hasn't submitted any assignments yet.
        </p>
      </div>
    );
  }

  const groups = groupBySubject(records);

  return (
    <div className="space-y-5">
      {groups.map((group) => (
        <div
          key={`${group.subjectName}|${group.classroomDisplay}`}
          className="bg-white rounded-xl border border-gray-200 p-5"
        >
          <div className="mb-4">
            <h3 className="font-semibold text-gray-900">{group.subjectName}</h3>
            <p className="text-sm text-gray-500">{group.classroomDisplay}</p>
          </div>
          <div className="divide-y divide-gray-50">
            {group.records.map((r) => (
              <ProficiencyBar key={r.id} record={r} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export const ParentDashboard = () => {
  const { data: children, isLoading } = useChildren();
  const [selectedChildId, setSelectedChildId] = useState<number | undefined>();

  const effectiveChildId = selectedChildId ?? children?.[0]?.id;
  const selectedChild = children?.find((c) => c.id === effectiveChildId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!children || children.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Parent Dashboard</h1>
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 font-medium">No children linked to your account</p>
          <p className="text-sm text-gray-400 mt-1">
            Ask the school admin to link your children's accounts.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Parent Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Monitor your children's learning progress.</p>
      </div>

      {children.length > 1 && (
        <div className="flex gap-2 flex-wrap mb-6">
          {children.map((child) => (
            <button
              key={child.id}
              onClick={() => setSelectedChildId(child.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                child.id === effectiveChildId
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {child.first_name || child.username}
              {child.grade != null && (
                <span className="ml-1 opacity-70">Gr.{child.grade}</span>
              )}
            </button>
          ))}
        </div>
      )}

      {selectedChild && (
        <>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-800">
              {selectedChild.first_name || selectedChild.username}'s Progress
            </h2>
            {selectedChild.grade != null && (
              <p className="text-sm text-gray-500">Grade {selectedChild.grade}</p>
            )}
          </div>
          <ChildView child={selectedChild} />
        </>
      )}
    </div>
  );
};
