import { useProficiency } from './useProficiency';
import { LoadingSpinner } from '@/shared/components/LoadingSpinner';
import type { StudentProficiency } from '@/types/index';

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
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <span className="text-sm font-medium text-gray-800 truncate">{record.tag_name}</span>
          <span className="text-sm font-semibold text-gray-700 shrink-0">{pct}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Based on {record.tick_count} question{record.tick_count !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
};

export const ProficiencyPage = () => {
  const { data: records, isLoading } = useProficiency();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!records || records.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Progress</h1>
        <p className="text-sm text-gray-500 mb-8">Your proficiency per topic, updated after each submission.</p>
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500 font-medium">No progress yet</p>
          <p className="text-sm text-gray-400 mt-1">Complete an assignment to see your progress here.</p>
        </div>
      </div>
    );
  }

  const groups = groupBySubject(records);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">My Progress</h1>
      <p className="text-sm text-gray-500 mb-8">Your proficiency per topic, updated after each submission.</p>

      <div className="space-y-6">
        {groups.map((group) => (
          <div key={`${group.subjectName}|${group.classroomDisplay}`} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="mb-4">
              <h2 className="font-semibold text-gray-900">{group.subjectName}</h2>
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
    </div>
  );
};
