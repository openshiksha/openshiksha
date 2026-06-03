import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubjectRooms, type TeacherSubjectRoom } from './useSubjectRooms';
import { useProblemSets, type TeacherProblemSet } from './useProblemSets';
import { useCreateAssignment } from './useCreateAssignment';
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

const formatDueDate = (iso: string): string => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
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
    return [make(3, '3 days'), make(7, '1 week'), make(14, '2 weeks')];
  }, []);

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
          title="Assignment created!"
          description={
            <>
              {selectedRoom && (
                <>
                  <strong className="text-ink-700">{selectedRoom.student_count}</strong>{' '}
                  {selectedRoom.student_count === 1 ? 'student' : 'students'} in{' '}
                  <strong className="text-ink-700">{selectedRoom.classroom_display}</strong> can
                  now see it on their dashboard. Due{' '}
                  <strong className="text-ink-700">{formatDueDate(dueDate)}</strong>.
                </>
              )}
            </>
          }
          action={
            <div className="flex flex-wrap justify-center gap-3">
              <Button onClick={() => navigate('/teacher')}>Back to dashboard</Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setSubjectRoomId('');
                  setProblemSetId('');
                  setDueDate('');
                  setSuccessAssignmentId(null);
                }}
              >
                Create another
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  const daysOut = daysFromToday(dueDate);

  // ── Main UI ──────────────────────────────────────────────────────────────
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 lg:px-6">
      {/* Header */}
      <SectionHeading
        as="h1"
        eyebrow="Authoring"
        title="Create Assignment"
        description="Assign a problem set to one of your subject rooms. Students see it instantly."
        action={
          <button
            type="button"
            onClick={() => navigate('/teacher')}
            className="text-sm font-medium text-ink-500 hover:text-ink-800"
          >
            ← Back
          </button>
        }
      />

      <form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-12">
        {/* Form column */}
        <div className="space-y-4 lg:col-span-5 xl:col-span-4">
          {/* Step 1: Class */}
          <Card>
            <div className="mb-4 flex items-center gap-3">
              <StepDot index={1} active />
              <h2 className="font-display text-lg font-semibold text-ink-900">Choose class</h2>
            </div>
            {roomsLoading ? (
              <Skeleton className="h-10 w-full rounded-lg" />
            ) : !subjectRooms || subjectRooms.length === 0 ? (
              <p className="text-sm text-ink-500">
                You don&apos;t teach any subject rooms yet.
              </p>
            ) : (
              <Select
                label="Subject room"
                value={subjectRoomId}
                onChange={(e) => {
                  setSubjectRoomId(e.target.value ? Number(e.target.value) : '');
                  setProblemSetId('');
                }}
              >
                <option value="">Select a class…</option>
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
              <h2 className="font-display text-lg font-semibold text-ink-900">Pick problem set</h2>
            </div>
            {subjectRoomId === '' ? (
              <p className="text-sm text-ink-400">Choose a class first.</p>
            ) : setsLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full rounded-lg" />
                <Skeleton className="h-12 w-full rounded-lg" />
              </div>
            ) : !problemSets || problemSets.length === 0 ? (
              <div className="rounded-xl border border-dashed border-ink-200 bg-paper p-5 text-center">
                <p className="text-sm text-ink-500">
                  No problem sets for{' '}
                  <strong className="text-ink-700">{selectedRoom?.subject_name}</strong> yet.
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-3"
                  onClick={() => navigate('/teacher/problem-sets/new')}
                >
                  + Build one
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
              <h2 className="font-display text-lg font-semibold text-ink-900">Set due date</h2>
            </div>
            <Input
              type="date"
              label="Due date"
              value={dueDate}
              min={minDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
            <div className="mt-3 flex flex-wrap items-center gap-1.5">
              <span className="mr-1 text-xs font-medium text-ink-500">Quick set:</span>
              {datePresets.map((p) => (
                <button
                  key={p.iso}
                  type="button"
                  onClick={() => setDueDate(p.iso)}
                  className={[
                    'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium transition-colors',
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
                Due in{' '}
                <strong className="text-ink-700">
                  {daysOut === 0 ? 'today' : `${daysOut} day${daysOut === 1 ? '' : 's'}`}
                </strong>
                {' · '}
                {formatDueDate(dueDate)}
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
}) => (
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
          {questionCount} {questionCount === 1 ? 'question' : 'questions'}
        </Badge>
        {estimatedMinutes && (
          <span className="text-xs text-ink-500">~{estimatedMinutes} min</span>
        )}
      </div>
    </div>
  </button>
);

interface AssignmentPreviewProps {
  room: TeacherSubjectRoom | null;
  set: TeacherProblemSet | null;
  dueDate: string;
  valid: boolean;
  submitting: boolean;
  error: boolean;
}

const AssignmentPreview = ({ room, set, dueDate, valid, submitting, error }: AssignmentPreviewProps) => {
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
          Your assignment preview
        </h3>
        <p className="mt-1 max-w-sm text-sm text-ink-500">
          Pick a class, a problem set, and a due date — you&apos;ll see exactly what students see
          here before you publish.
        </p>
      </Card>
    );
  }

  const daysOut = daysFromToday(dueDate);
  const dueText = dueDate
    ? `Due ${formatDueDate(dueDate)}${
        daysOut !== null && daysOut >= 0
          ? ` · ${daysOut === 0 ? 'today' : `${daysOut} day${daysOut === 1 ? '' : 's'} from now`}`
          : ''
      }`
    : 'No due date set yet';

  return (
    <Card className="flex h-full min-h-[28rem] flex-col">
      {/* Hero strip */}
      <div className="-m-6 mb-5 rounded-t-xl2 border-b border-ink-100 bg-chalkboard p-6 text-white">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-300">
          Assignment preview
        </p>
        <h3 className="mt-1 font-display text-2xl font-semibold text-balance">
          {set?.title ?? <span className="text-ink-300">Pick a problem set</span>}
        </h3>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-ink-100">
          <span className="inline-flex items-center gap-1.5">
            <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="currentColor">
              <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm-5 6a5 5 0 0110 0v1H3v-1z" />
            </svg>
            {room.classroom_display}
          </span>
          <span className="opacity-50">·</span>
          <span>{room.student_count} {room.student_count === 1 ? 'student' : 'students'}</span>
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
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brand-600">
            What students will see
          </p>
          {set ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-ink-900">{set.title}</p>
              {set.description && (
                <p className="text-sm text-ink-600">{set.description}</p>
              )}
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="brand">
                  {set.question_count} {set.question_count === 1 ? 'question' : 'questions'}
                </Badge>
                {set.estimated_minutes && (
                  <Badge tone="neutral">~{set.estimated_minutes} min</Badge>
                )}
                <Badge tone="neutral">{set.chapter_name}</Badge>
              </div>
            </div>
          ) : (
            <p className="text-sm text-ink-400">Pick a problem set on the left.</p>
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
            <p className="text-xs font-semibold uppercase tracking-widest text-ink-500">Due</p>
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
              Recipients
            </p>
            <p className="text-sm font-medium text-ink-900">
              {room.student_count} {room.student_count === 1 ? 'student' : 'students'} in{' '}
              {room.classroom_display}
            </p>
          </div>
        </div>
      </div>

      {/* Action footer */}
      <div className="-mx-6 -mb-6 mt-5 flex items-center justify-between gap-3 rounded-b-xl2 border-t border-ink-100 bg-paper px-6 py-4">
        <div className="text-xs text-ink-500">
          {!valid ? (
            'Complete all three steps to publish.'
          ) : (
            <>
              Ready to publish to{' '}
              <strong className="text-ink-700">
                {room.student_count} {room.student_count === 1 ? 'student' : 'students'}
              </strong>
              .
            </>
          )}
          {error && (
            <span className="ml-2 font-medium text-rose-600">
              Failed to create. Please try again.
            </span>
          )}
        </div>
        <Button type="submit" size="lg" disabled={!valid || submitting}>
          {submitting && <LoadingSpinner size="sm" />}
          {submitting ? 'Publishing…' : 'Publish Assignment'}
        </Button>
      </div>
    </Card>
  );
};
