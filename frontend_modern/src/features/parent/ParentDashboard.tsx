import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useChildren } from './useChildren';
import { useChildProficiency } from './useChildProficiency';
import { useChildAssignments } from './useChildAssignments';
import { Badge, Card, EmptyState, LoadingSpinner, SectionHeading } from '@/shared/ui';
import { useI18n, useT } from '@/shared/i18n';
import type { User, StudentProficiency, Assignment } from '@/types/index';

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
  const t = useT();
  const pct = Math.round(record.score * 100);
  const barColor = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-amber-400' : 'bg-rose-400';

  return (
    <div className="py-2.5">
      <div className="flex items-baseline justify-between gap-2 mb-1">
        <span className="text-sm font-medium text-ink-800 truncate">{record.tag_name}</span>
        <span className="text-sm font-semibold text-ink-700 shrink-0">{pct}%</span>
      </div>
      <div className="h-2 bg-ink-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 motion-reduce:transition-none ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-ink-400 mt-1">
        {t(record.tick_count === 1 ? 'parent.questionsPractisedOne' : 'parent.questionsPractisedMany', {
          count: record.tick_count,
        })}
      </p>
    </div>
  );
};

const ChildView = ({ child }: { child: User }) => {
  const t = useT();
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
      <EmptyState
        title={t('parent.noProgressTitle')}
        description={t('parent.noProgressDescription', { name: child.first_name || child.username })}
      />
    );
  }

  const groups = groupBySubject(records);

  return (
    <div className="space-y-5">
      {groups.map((group) => (
        <Card key={`${group.subjectName}|${group.classroomDisplay}`} className="p-5">
          <div className="mb-4">
            <h3 className="font-display font-semibold text-ink-900">{group.subjectName}</h3>
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
  );
};

const AssignmentStatusBadge = ({
  status,
  isOverdue,
}: {
  status: Assignment['child_submission_status'];
  isOverdue: boolean;
}) => {
  const t = useT();
  if (status === 'submitted') return <Badge tone="success">{t('parent.statusSubmitted')}</Badge>;
  if (isOverdue) return <Badge tone="urgent">{t('parent.statusOverdue')}</Badge>;
  return <Badge tone="attention">{t('parent.statusPending')}</Badge>;
};

const ChildAssignmentsView = ({ child }: { child: User }) => {
  const { t, locale } = useI18n();
  const { data: assignments, isLoading } = useChildAssignments(child.id);

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  if (!assignments || assignments.length === 0) {
    return (
      <EmptyState
        title={t('assignments.emptyTitle')}
        description={t('parent.noAssignmentsDescription')}
      />
    );
  }

  const now = new Date();
  const sorted = [...assignments].sort(
    (a, b) => new Date(a.due_at).getTime() - new Date(b.due_at).getTime(),
  );

  return (
    <div className="space-y-3">
      {sorted.map((a) => {
        const dueDate = new Date(a.due_at);
        const isOverdue = dueDate < now;
        const isSubmitted = a.child_submission_status === 'submitted';
        const dueFmt = dueDate.toLocaleDateString(locale === 'hi' ? 'hi-IN' : 'en-IN', {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        });

        return (
          <Card key={a.id} className="p-4 hover:shadow-xs transition-shadow motion-reduce:transition-none">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-ink-900 truncate">{a.problem_set.title}</p>
                <p className="text-sm text-ink-500 mt-0.5">{a.subject_room_display}</p>
              </div>
              <AssignmentStatusBadge status={a.child_submission_status} isOverdue={isOverdue && !isSubmitted} />
            </div>
            <p
              className={`text-xs mt-2 ${
                isOverdue && !isSubmitted ? 'text-rose-600 font-medium' : 'text-ink-400'
              }`}
            >
              {isOverdue && !isSubmitted
                ? t('parent.overdueOn', { date: dueFmt })
                : t('parent.dueOn', { date: dueFmt })}
            </p>
          </Card>
        );
      })}
    </div>
  );
};

export const ParentDashboard = () => {
  const t = useT();
  const { data: children, isLoading } = useChildren();
  const [selectedChildId, setSelectedChildId] = useState<number | undefined>();
  const [activeTab, setActiveTab] = useState<'progress' | 'assignments'>('progress');

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
        <SectionHeading as="h1" title={t('parent.title')} className="mb-6" />
        <EmptyState
          title={t('parent.noChildrenTitle')}
          description={t('parent.noChildrenDescription')}
        />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <SectionHeading
        as="h1"
        title={t('parent.title')}
        description={t('parent.description')}
        className="mb-6"
      />

      {children.length > 1 && (
        <div className="flex gap-2 flex-wrap mb-6">
          {children.map((child) => (
            <button
              key={child.id}
              onClick={() => setSelectedChildId(child.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 ${
                child.id === effectiveChildId
                  ? 'bg-brand-600 text-white'
                  : 'bg-white border border-ink-200 text-ink-700 hover:bg-brand-50'
              }`}
            >
              {child.first_name || child.username}
              {child.grade != null && (
                <span className="ml-1 opacity-70">
                  {t('parent.gradeShort', { grade: child.grade })}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {selectedChild && (
        <>
          <div className="mb-4 flex items-start justify-between gap-3 flex-wrap">
            <div>
              <h2 className="text-lg font-display font-semibold text-ink-800">
                {t('parent.overview', { name: selectedChild.first_name || selectedChild.username })}
              </h2>
              {selectedChild.grade != null && (
                <p className="text-sm text-ink-500">
                  {t('parent.grade', { grade: selectedChild.grade })}
                </p>
              )}
            </div>
            <Link
              to={`/parent/insights/${selectedChild.id}`}
              className="shrink-0 px-3 py-2 text-sm font-semibold rounded-lg bg-brand-50 text-brand-800 hover:bg-brand-100 transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
            >
              {t('parent.viewInsights')}
            </Link>
          </div>

          {/* Tab switcher with chalk underline */}
          <div className="flex gap-1 mb-6 border-b border-ink-200">
            {(['progress', 'assignments'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors motion-reduce:transition-none focus:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 ${
                  activeTab === tab
                    ? 'border-brand-600 text-brand-700 chalk-underline'
                    : 'border-transparent text-ink-500 hover:text-ink-700'
                }`}
              >
                {tab === 'progress' ? t('parent.tabProgress') : t('parent.tabAssignments')}
              </button>
            ))}
          </div>

          {activeTab === 'progress' && <ChildView child={selectedChild} />}
          {activeTab === 'assignments' && <ChildAssignmentsView child={selectedChild} />}
        </>
      )}
    </div>
  );
};
