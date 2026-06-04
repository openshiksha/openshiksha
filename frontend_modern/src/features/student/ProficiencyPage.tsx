import { useProficiency } from './useProficiency';
import { useProficiencyHistory } from './useProficiencyHistory';
import { Card, EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';
import { TrendSparkline } from '@/shared/components/TrendSparkline';
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

// Unlock motif: mastery (>=70%) reads as "unlocked" in brand orange;
// approaching uses amber, struggling uses rose. Track is warm ink-100.
const ProficiencyBar = ({ record }: { record: StudentProficiency }) => {
  const pct = Math.round(record.score * 100);
  const isMastered = pct >= 70;
  const barColor = isMastered ? 'bg-brand-600' : pct >= 40 ? 'bg-amber-400' : 'bg-rose-400';
  const { data: history } = useProficiencyHistory({
    tagId: record.question_tag,
    subjectRoomId: record.subject_room,
  });

  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <span className="text-sm font-medium text-ink-800 truncate flex items-center gap-1.5">
            {isMastered && (
              <span aria-label="Mastered" title="Topic unlocked" className="text-brand-600">
                ✓
              </span>
            )}
            {record.tag_name}
          </span>
          <div className="flex items-center gap-2 shrink-0">
            {history && history.length >= 2 && <TrendSparkline snapshots={history} />}
            <span className="text-sm font-semibold text-ink-700">{pct}%</span>
          </div>
        </div>
        <div className="h-2 bg-ink-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all motion-reduce:transition-none ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-ink-400 mt-1">
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
        <SectionHeading
          as="h1"
          title="My Progress"
          description="Your proficiency per topic, updated after each submission."
          className="mb-6"
        />
        <EmptyState
          title="No progress yet"
          description="Complete an assignment to see your progress here."
        />
      </div>
    );
  }

  const groups = groupBySubject(records);

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <SectionHeading
        as="h1"
        title="My Progress"
        description="Your proficiency per topic, updated after each submission."
        className="mb-8"
      />

      <div className="space-y-6">
        {groups.map((group) => (
          <Card key={`${group.subjectName}|${group.classroomDisplay}`} className="p-5">
            <div className="mb-4">
              <h2 className="font-display font-semibold text-ink-900">{group.subjectName}</h2>
              <p className="text-sm text-ink-500">{group.classroomDisplay}</p>
            </div>
            <div className="divide-y divide-ink-100">
              {group.records.map((r) => (
                <ProficiencyBar key={r.id} record={r} />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
