import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSubjectRooms, type TeacherSubjectRoom } from './useSubjectRooms';
import { useProblemSets, type TeacherProblemSet } from './useProblemSets';
import { useCreateAssignment } from './useCreateAssignment';
import { useT, useI18n, formatDate, type Locale } from '@/shared/i18n';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  LoadingSpinner,
  SectionHeading,
  Select,
  Skeleton,
} from '@/shared/ui';

// ── Pretty due-date helpers ────────────────────────────────────────────────

// Absolute due-date in the active locale via the shared LA-8 `formatDate`
// helper (so a Hindi-medium teacher sees "बुधवार, 27 मई 2026", not English).
const formatDueDate = (iso: string, locale: Locale): string => {
  if (!iso) return '';
  return formatDate(iso, locale, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
};

const daysFromToday = (iso: string): number | null => {
  if (!iso) return null;
  try {
    const due = new Date(iso);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diff = Math.round((due.getTime() - today.getTime()) / 86_400_000);
    return diff;
  } catch {
    return null;
  }
};

// ── Page ───────────────────────────────────────────────────────────────────

export const CreateAssignmentPage = () => {
  const navigate = useNavigate();
  const t = useT();
  const { locale } = useI18n();
  const [searchParams] = useSearchParams();

  const [subjectRoomId, setSubjectRoomId] = useState<number | ''>('');
  const [problemSetId, setProblemSetId] = useState<number | ''>('');
  const [dueDate, setDueDate] = useState('');
  const [successAssignmentId, setSuccessAssignmentId] = useState<number | null>(null);

  const { data: subjectRooms, isLoading: roomsLoading } = useSubjectRooms();

  const selectedRoom = useMemo(
    () => subjectRooms?.find((r) => r.id === subjectRoomId) ?? null,
    [subjectRooms, subjectRoomId],
  );
  const subjectId = selectedRoom?.subject ?? null;

  const { data: problemSets, isLoading: setsLoading } = useProblemSets(subjectId);

  // ── Deep-link preselection ────────────────────────────────────────────────
  // The dashboard's "Assign" buttons link here with ?room=<id> (from a subject
  // room) or ?problemSet=<id> (from a problem set). We resolve the set's subject
  // from the unfiltered list so a ?problemSet= link can pick a matching room
  // even before the subject-filtered list loads.
  //
  // This is the "adjust state when data arrives" case, so we apply it during
  // render (guarded so it runs once) rather than in an effect — see
  // https://react.dev/learn/you-might-not-need-an-effect. The guards flip only
  // after the relevant data has loaded, so a teacher's later manual edits stick.
  const presetRoom = searchParams.get('room');
  const presetSet = searchParams.get('problemSet');
  const { data: allSets } = useProblemSets();
  const [roomPresetDone, setRoomPresetDone] = useState(false);
  const [setPresetDone, setSetPresetDone] = useState(false);

  if (!roomPresetDone && subjectRooms) {
    if (presetRoom) {
      const rid = Number(presetRoom);
      if (subjectRooms.some((r) => r.id === rid)) setSubjectRoomId(rid);
      setRoomPresetDone(true);
    } else if (presetSet && allSets) {
      const target = allSets.find((s) => s.id === Number(presetSet));
      if (target) {
        const room = subjectRooms.find((r) => r.subject === target.subject);
        if (room) setSubjectRoomId(room.id);
      }
      setRoomPresetDone(true);
    } else if (!presetSet) {
      setRoomPresetDone(true);
    }
  }

  if (!setPresetDone && presetSet && problemSets) {
    const id = Number(presetSet);
    if (problemSets.some((s) => s.id === id)) {
      setProblemSetId(id);
      setSetPresetDone(true);
    }
  }

  const selectedSet = useMemo(
    () => problemSets?.find((ps) => ps.id === problemSetId) ?? null,
    [problemSets, problemSetId],
  );

  const createAssignment = useCreateAssignment();

  const isFormValid = subjectRoomId !== '' && problemSetId !== '' && dueDate !== '';

  const minDate = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  }, []);

  // Quick due-date presets
  const datePresets = useMemo(() => {
    const make = (days: number, label: string) => {
      const d = new Date();
      d.setDate(d.getDate() + days);
      return { iso: d.toISOString().split('T')[0], label };
    };
    return [
      make(3, t('assignForm.preset3days')),
      make(7, t('assignForm.preset1week')),
      make(14, t('assignForm.preset2weeks')),
    ];
  }, [t]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;
    createAssignment.mutate(
      {
        subject_room: subjectRoomId as number,
        problem_set_id: problemSetId as number,
        due_at: new Date(dueDate).toISOString(),
      },
      {
        onSuccess: (result) => setSuccessAssignmentId(result.id),
      },
    );
  };

  // ── Success state ────────────────────────────────────────────────────────
  if (successAssignmentId !== null) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <EmptyState
          title={t('assignForm.successTitle')}
          description={
            <>
              {selectedRoom &&
                t(
                  selectedRoom.student_count === 1
                    ? 'assignForm.successBodyOne'
                    : 'assignForm.successBodyMany',
                  {
                    count: selectedRoom.student_count,
                    room: selectedRoom.classroom_display,
                    date: formatDueDate(dueDate, locale),
                  },
                )}
            </>
          }
          action={
            <div className="flex flex-wrap justify-center gap-3">
              <Button onClick={() => navigate('/teacher')}>
                {t('assignForm.backToDashboard')}
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setSubjectRoomId('');
                  setProblemSetId('');
                  setDueDate('');
                  setSuccessAssignmentId(null);
                }}
              >
                {t('assignForm.createAnother')}
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  const daysOut = daysFromToday(dueDate);

  // ── Main UI ──────────────────────────────────────────────────────────────
  // Extra bottom padding on small screens leaves room for the sticky mobile
  // action bar so the last form field doesn't sit underneath it.
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 pb-28 lg:px-6 lg:pb-8">
      {/* Header */}
      <SectionHeading
        as="h1"
        eyebrow={t('assignForm.eyebrow')}
        title={t('assignForm.title')}
        description={t('assignForm.description')}
        action={
          <button
            type="button"
            onClick={() => navigate('/teacher')}
            className="text-sm font-medium text-ink-500 hover:text-ink-800"
          >
            {t('assignForm.back')}
          </button>
        }
      />

      <form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-12" data-testid="create-assignment-form">
        {/* Form column */}
        <div className="space-y-4 lg:col-span-5 xl:col-span-4">
          {/* Step 1: Class */}
          <Card>
            <div className="mb-4 flex items-center gap-3">
              <StepDot index={1} active />
              <h2 className="font-display text-lg font-semibold text-ink-900">
                {t('assignForm.stepClass')}
              </h2>
            </div>
            {roomsLoading ? (
              <Skeleton className="h-10 w-full rounded-lg" />
            ) : !subjectRooms || subjectRooms.length === 0 ? (
              <p className="text-sm text-ink-500">{t('assignForm.noRooms')}</p>
            ) : (
              <Select
                label={t('assignForm.subjectRoomLabel')}
                value={subjectRoomId}
                onChange={(e) => {
                  setSubjectRoomId(e.target.value ? Number(e.target.value) : '');
                  setProblemSetId('');
                }}
              >
                <option value="">{t('assignForm.selectClass')}</option>
                {subjectRooms.map((room) => (
                  <option key={room.id} value={room.id}>
                    {room.subject_name} — {room.classroom_display}
                  </option>
                ))}
              </Select>
            )}
          </Card>

          {/* Step 2: Problem set */}
          <Card>
            <div className="mb-4 flex items-center gap-3">
              <StepDot index={2} active={subjectRoomId !== ''} />
              <h2 className="font-display text-lg font-semibold text-ink-900">
                {t('assignForm.stepProblemSet')}
              </h2>
            </div>
            {subjectRoomId === '' ? (
              <p className="text-sm text-ink-400">{t('assignForm.chooseClassFirst')}</p>
            ) : setsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full rounded-lg" />
                <Skeleton className="h-12 w-full rounded-lg" />
              </div>
            ) : !problemSets || problemSets.length === 0 ? (
              <div className="rounded-xl border border-dashed border-ink-200 bg-paper p-5 text-center">
                <p className="text-sm text-ink-500">
                  {t('assignForm.noSetsForSubject', {
                    subject: selectedRoom?.subject_name ?? '',
                  })}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-3"
                  onClick={() => navigate('/teacher/problem-sets/new')}
                >
                  {t('assignForm.buildOne')}
                </Button>
              </div>
            ) : (
              <div className="max-h-[20rem] space-y-2 overflow-y-auto pr-1">
                {problemSets.map((ps) => (
                  <ProblemSetRow
                    key={ps.id}
                    title={ps.title}
                    questionCount={ps.question_count}
                    estimatedMinutes={ps.estimated_minutes}
                    chapterName={ps.chapter_name}
                    selected={problemSetId === ps.id}
                    onSelect={() => setProblemSetId(ps.id)}
                  />
                ))}
              </div>
            )}
          </Card>

          {/* Step 3: Due date */}
          <Card>
            <div className="mb-4 flex items-center gap-3">
              <StepDot index={3} active={problemSetId !== ''} />
              <h2 className="font-display text-lg font-semibold text-ink-900">
                {t('assignForm.stepDueDate')}
              </h2>
            </div>
            <Input
              type="date"
              label={t('assignForm.dueDateLabel')}
              value={dueDate}
              min={minDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="mr-1 text-xs font-medium text-ink-500">
                {t('assignForm.quickSet')}
              </span>
              {datePresets.map((p) => (
                <button
                  key={p.iso}
                  type="button"
                  onClick={() => setDueDate(p.iso)}
                  className={[
                    // ~44px tall on mobile (touch-target spec); slimmer on desktop.
                    'inline-flex items-center rounded-full px-4 py-2 text-sm font-medium transition-colors sm:px-3 sm:py-1 sm:text-xs',
                    dueDate === p.iso
                      ? 'bg-brand-600 text-white shadow-soft'
                      : 'bg-ink-50 text-ink-700 hover:bg-ink-100',
                  ].join(' ')}
                >
                  {p.label}
                </button>
              ))}
            </div>
            {daysOut !== null && daysOut >= 0 && (
              <p className="mt-3 text-xs text-ink-500">
                {daysOut === 0
                  ? t('assignForm.dueTodayHint', { date: formatDueDate(dueDate, locale) })
                  : t(
                      daysOut === 1
                        ? 'assignForm.dueInDaysHintOne'
                        : 'assignForm.dueInDaysHintMany',
                      { count: daysOut, date: formatDueDate(dueDate, locale) },
                    )}
              </p>
            )}
          </Card>
        </div>

        {/* Preview column */}
        <div className="lg:col-span-7 xl:col-span-8">
          <AssignmentPreview
            room={selectedRoom}
            set={selectedSet}
            dueDate={dueDate}
            valid={isFormValid}
            submitting={createAssignment.isPending}
            error={createAssignment.isError}
          />
        </div>

        {/* Sticky mobile action bar — desktop has the publish button inside
            the preview Card; on phones the preview is too long to scroll to,
            so we surface the same action above the system nav. */}
        <div
          className="fixed inset-x-0 bottom-0 z-30 border-t border-ink-100 bg-paper/95 px-4 py-3 shadow-lift backdrop-blur lg:hidden"
          data-testid="mobile-publish-bar"
        >
          <Button
            type="submit"
            size="lg"
            disabled={!isFormValid || createAssignment.isPending}
            className="w-full"
          >
            {createAssignment.isPending && <LoadingSpinner size="sm" />}
            {createAssignment.isPending
              ? t('assignForm.publishing')
              : t('assignForm.publish')}
          </Button>
          {!isFormValid && (
            <p className="mt-1.5 text-center text-xs text-ink-500">
              {t('assignForm.completeAllSteps')}
            </p>
          )}
        </div>
      </form>
    </div>
  );
};

// ── Sub-components ─────────────────────────────────────────────────────────

const StepDot = ({ index, active }: { index: number; active: boolean }) => (
  <span
    aria-hidden="true"
    className={[
      'inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
      active ? 'bg-brand-600 text-white shadow-soft' : 'bg-ink-100 text-ink-500',
    ].join(' ')}
  >
    {index}
  </span>
);

const ProblemSetRow = ({
  title,
  questionCount,
  estimatedMinutes,
  chapterName,
  selected,
  onSelect,
}: {
  title: string;
  questionCount: number;
  estimatedMinutes: number | null;
  chapterName: string;
  selected: boolean;
  onSelect: () => void;
}) => {
  const t = useT();
  return (
  <button
    type="button"
    onClick={onSelect}
    className={[
      'group flex w-full items-start gap-3 rounded-lg p-3 text-left transition-all',
      selected
        ? 'bg-brand-50 ring-1 ring-brand-300 shadow-soft'
        : 'ring-1 ring-transparent hover:bg-ink-50 hover:ring-ink-100',
    ].join(' ')}
  >
    <span
      className={[
        'mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors',
        selected ? 'border-brand-600 bg-brand-600' : 'border-ink-300 bg-white',
      ].join(' ')}
    >
      {selected && (
        <svg viewBox="0 0 12 12" className="h-3 w-3 text-white" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M2.5 6.5l2.5 2.5 4.5-5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </span>
    <div className="min-w-0 flex-1">
      <p className="line-clamp-2 text-sm font-medium text-ink-900">{title}</p>
      <p className="mt-0.5 text-xs text-ink-500">{chapterName}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2">
        <Badge tone="brand">
          {t(questionCount === 1 ? 'teacher.questionsCountOne' : 'teacher.questionsCountMany', {
            count: questionCount,
          })}
        </Badge>
        {estimatedMinutes && (
          <span className="text-xs text-ink-500">
            {t('teacher.minutesApprox', { minutes: estimatedMinutes })}
          </span>
        )}
      </div>
    </div>
  </button>
  );
};

interface AssignmentPreviewProps {
  room: TeacherSubjectRoom | null;
  set: TeacherProblemSet | null;
  dueDate: string;
  valid: boolean;
  submitting: boolean;
  error: boolean;
}

const AssignmentPreview = ({ room, set, dueDate, valid, submitting, error }: AssignmentPreviewProps) => {
  const t = useT();
  const { locale } = useI18n();
  // Empty state when nothing is picked yet
  if (!room) {
    return (
      <Card className="flex h-full min-h-[28rem] flex-col items-center justify-center text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-50">
          <svg viewBox="0 0 64 64" className="h-9 w-9 text-brand-500" fill="none">
            <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="2" opacity="0.2" />
            <circle cx="32" cy="26" r="7" stroke="currentColor" strokeWidth="3" />
            <path
              d="M28 31 L26 44 L38 44 L36 31"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h3 className="font-display text-lg font-semibold text-ink-900">
          {t('assignForm.previewEmptyTitle')}
        </h3>
        <p className="mt-1 max-w-sm text-sm text-ink-500">
          {t('assignForm.previewEmptyBody')}
        </p>
      </Card>
    );
  }

  const daysOut = daysFromToday(dueDate);
  const formattedDue = formatDueDate(dueDate, locale);
  let dueText: string;
  if (!dueDate) {
    dueText = t('assignForm.noDueYet');
  } else if (daysOut === 0) {
    dueText = t('assignForm.dueOnTodaySuffix', { date: formattedDue });
  } else if (daysOut !== null && daysOut > 0) {
    dueText = t(
      daysOut === 1 ? 'assignForm.dueOnDaysSuffixOne' : 'assignForm.dueOnDaysSuffixMany',
      { date: formattedDue, count: daysOut },
    );
  } else {
    dueText = t('assignForm.dueOn', { date: formattedDue });
  }

  return (
    <Card className="flex h-full min-h-[28rem] flex-col">
      {/* Hero strip */}
      <div className="-m-6 mb-5 rounded-t-xl2 border-b border-ink-100 bg-chalkboard p-6 text-white">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-300">
          {t('assignForm.previewEyebrow')}
        </p>
        <h3 className="mt-1 font-display text-2xl font-semibold text-balance">
          {set?.title ?? <span className="text-ink-300">{t('assignForm.pickProblemSet')}</span>}
        </h3>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-ink-100">
          <span className="inline-flex items-center gap-1.5">
            <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor">
              <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-5 6a5 5 0 0110 0v1H3v-1z" />
            </svg>
            {room.classroom_display}
          </span>
          <span className="opacity-50">·</span>
          <span>
            {t(room.student_count === 1 ? 'teacher.studentsCountOne' : 'teacher.studentsCountMany', {
              count: room.student_count,
            })}
          </span>
          {set && (
            <>
              <span className="opacity-50">·</span>
              <span>{set.subject_name}</span>
            </>
          )}
        </div>
      </div>

      {/* Detail cards */}
      <div className="flex-1 space-y-4">
        {/* What students will see */}
        <div className="rounded-xl border border-ink-100 bg-paper p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brand-700">
            {t('assignForm.whatStudentsSee')}
          </p>
          {set ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-ink-900">{set.title}</p>
              {set.description && (
                <p className="text-sm text-ink-600">{set.description}</p>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="brand">
                  {t(
                    set.question_count === 1
                      ? 'teacher.questionsCountOne'
                      : 'teacher.questionsCountMany',
                    { count: set.question_count },
                  )}
                </Badge>
                {set.estimated_minutes && (
                  <Badge tone="neutral">
                    {t('teacher.minutesApprox', { minutes: set.estimated_minutes })}
                  </Badge>
                )}
                <Badge tone="neutral">{set.chapter_name}</Badge>
              </div>
              <a
                href={`/teacher/problem-sets/${set.id}/preview`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800"
              >
                {t('assignForm.previewQuestionsLink')}
                <span aria-hidden="true">↗</span>
              </a>
            </div>
          ) : (
            <p className="text-sm text-ink-400">{t('assignForm.pickSetLeft')}</p>
          )}
        </div>

        {/* Due date strip */}
        <div className="flex items-center gap-3 rounded-xl border border-ink-100 bg-white p-4 shadow-soft">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-700">
            <svg viewBox="0 0 16 16" className="h-5 w-5" fill="currentColor">
              <path d="M5 2v2H3a1 1 0 00-1 1v8a1 1 0 001 1h10a1 1 0 001-1V5a1 1 0 00-1-1h-2V2h-1v2H6V2H5zm-2 5h10v6H3V7z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-widest text-ink-500">
              {t('assignForm.dueLabel')}
            </p>
            <p className="text-sm font-medium text-ink-900">{dueText}</p>
          </div>
        </div>

        {/* Roster summary */}
        <div className="flex items-center gap-3 rounded-xl border border-ink-100 bg-white p-4 shadow-soft">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-700">
            <svg viewBox="0 0 16 16" className="h-5 w-5" fill="currentColor">
              <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-5 6a5 5 0 0110 0v1H3v-1z" />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-widest text-ink-500">
              {t('assignForm.recipients')}
            </p>
            <p className="text-sm font-medium text-ink-900">
              {t(
                room.student_count === 1
                  ? 'assignForm.recipientsValueOne'
                  : 'assignForm.recipientsValueMany',
                { count: room.student_count, room: room.classroom_display },
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Action footer */}
      <div className="-mx-6 -mb-6 mt-5 flex items-center justify-between gap-3 rounded-b-xl2 border-t border-ink-100 bg-paper px-6 py-4">
        <div className="text-xs text-ink-500">
          {!valid
            ? t('assignForm.completeAllSteps')
            : t(
                room.student_count === 1
                  ? 'assignForm.readyToPublishOne'
                  : 'assignForm.readyToPublishMany',
                { count: room.student_count },
              )}
          {error && (
            <span className="ml-2 font-medium text-rose-600">
              {t('assignForm.createFailed')}
            </span>
          )}
        </div>
        <Button type="submit" size="lg" disabled={!valid || submitting}>
          {submitting && <LoadingSpinner size="sm" />}
          {submitting ? t('assignForm.publishing') : t('assignForm.publish')}
        </Button>
      </div>
    </Card>
  );
};
