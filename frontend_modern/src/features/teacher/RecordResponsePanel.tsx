import { useState } from 'react';
import { Button, Skeleton } from '@/shared/ui';
import { useT } from '@/shared/i18n';
import { useSubjectRooms } from './useSubjectRooms';
import {
  useRoomStudents,
  useRubricForSubpart,
  useSaveRubric,
  useShortAnswerSubparts,
  useSubmitOpenResponse,
  type OpenResponseRubric,
  type RubricCriterion,
} from './useOpenRubrics';

interface RubricFormProps {
  subpartId: number;
  existing: OpenResponseRubric | null;
  onDone: () => void;
}

/**
 * Create or edit the one rubric a short-answer subpart carries: max marks,
 * the model answer the AI compares against, and optional per-point criteria
 * so partial credit is transparent.
 */
const RubricForm = ({ subpartId, existing, onDone }: RubricFormProps) => {
  const t = useT();
  const save = useSaveRubric();
  const [maxMarks, setMaxMarks] = useState(existing?.max_marks ?? 5);
  const [modelAnswer, setModelAnswer] = useState(existing?.model_answer ?? '');
  const [criteria, setCriteria] = useState<RubricCriterion[]>(existing?.criteria ?? []);

  const criteriaSum = criteria.reduce((sum, c) => sum + (c.marks || 0), 0);
  const sumMismatch = criteria.length > 0 && criteriaSum !== maxMarks;

  const updateCriterion = (i: number, patch: Partial<RubricCriterion>) =>
    setCriteria((rows) => rows.map((row, idx) => (idx === i ? { ...row, ...patch } : row)));

  return (
    <form
      className="mt-2 rounded-lg border border-ink-100 bg-ink-50/60 p-3 space-y-2"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate(
          {
            existingId: existing?.id ?? null,
            subpart: subpartId,
            max_marks: maxMarks,
            model_answer: modelAnswer,
            criteria: criteria.filter((c) => c.label.trim()),
          },
          { onSuccess: onDone }
        );
      }}
    >
      <label className="block text-xs text-ink-600">
        {t('recordResp.maxMarks')}
        <input
          type="number"
          min={1}
          max={100}
          value={maxMarks === 0 ? '' : maxMarks}
          onChange={(e) => {
            // Allow a transient empty field while retyping; clamp real values.
            const raw = e.target.value;
            setMaxMarks(raw === '' ? 0 : Math.min(100, Math.max(1, Number(raw) || 1)));
          }}
          className="input-brand mt-1 block w-24 text-sm"
        />
      </label>
      <label className="block text-xs text-ink-600">
        {t('recordResp.modelAnswer')} <span className="text-ink-400">{t('recordResp.modelAnswerHint')}</span>
        <textarea
          value={modelAnswer}
          onChange={(e) => setModelAnswer(e.target.value)}
          rows={3}
          className="input-brand mt-1 block w-full text-sm"
          placeholder={t('recordResp.modelAnswerPlaceholder')}
        />
      </label>

      <div>
        <p className="text-xs text-ink-600 font-medium">
          {t('recordResp.markingPoints')} <span className="text-ink-400 font-normal">{t('recordResp.markingPointsHint')}</span>
        </p>
        {criteria.map((c, i) => (
          <div key={i} className="mt-1.5 flex items-center gap-2">
            <input
              type="text"
              aria-label={t('recordResp.criterionLabelAria', { n: i + 1 })}
              value={c.label}
              onChange={(e) => updateCriterion(i, { label: e.target.value })}
              placeholder={t('recordResp.criterionLabelPlaceholder')}
              className="input-brand flex-1 text-sm"
            />
            <input
              type="number"
              aria-label={t('recordResp.criterionMarksAria', { n: i + 1 })}
              min={0}
              max={100}
              value={c.marks}
              onChange={(e) => updateCriterion(i, { marks: Number(e.target.value) || 0 })}
              className="input-brand w-20 text-sm"
            />
            <button
              type="button"
              aria-label={t('recordResp.removeCriterionAria', { n: i + 1 })}
              onClick={() => setCriteria((rows) => rows.filter((_, idx) => idx !== i))}
              className="text-ink-400 hover:text-rose-600 text-sm px-1 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-rose-400 rounded"
            >
              ✕
            </button>
          </div>
        ))}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="mt-1.5"
          onClick={() => setCriteria((rows) => [...rows, { label: '', marks: 1 }])}
        >
          {t('recordResp.addMarkingPoint')}
        </Button>
        {sumMismatch && (
          <p className="mt-1 text-xs text-amber-700">
            {t('recordResp.sumMismatch', { sum: criteriaSum, max: maxMarks })}
          </p>
        )}
      </div>

      {save.isError && (
        <p className="text-xs text-rose-600">
          {t('recordResp.saveError')}
        </p>
      )}

      <div className="flex gap-2 pt-1">
        <Button type="submit" variant="brand" size="sm" disabled={save.isPending || maxMarks < 1}>
          {save.isPending
            ? t('recordResp.saving')
            : existing
              ? t('recordResp.updateRubric')
              : t('recordResp.saveRubric')}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onDone}>
          {t('common.cancel')}
        </Button>
      </div>
    </form>
  );
};

const RubricSection = ({ subpartId }: { subpartId: number }) => {
  const t = useT();
  const { data: rubric, isLoading } = useRubricForSubpart(subpartId);
  const [editing, setEditing] = useState(false);

  if (isLoading) return <Skeleton w="w-2/3" h="h-4" className="mt-2" />;

  if (editing) {
    return (
      <RubricForm subpartId={subpartId} existing={rubric ?? null} onDone={() => setEditing(false)} />
    );
  }

  if (!rubric) {
    return (
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-amber-700">
        <span>{t('recordResp.noRubricWarning')}</span>
        <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(true)}>
          {t('recordResp.addRubric')}
        </Button>
      </div>
    );
  }

  return (
    <div className="mt-2 rounded-lg border border-ink-100 bg-paper p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-ink-600">
          <span className="font-semibold">{t('recordResp.rubricLabel')}</span>{' '}
          {t('recordResp.marksLabel', { count: rubric.max_marks })}
          {rubric.criteria.length > 0 &&
            ` · ${t(
              rubric.criteria.length === 1
                ? 'recordResp.markingPointsCountOne'
                : 'recordResp.markingPointsCountMany',
              { count: rubric.criteria.length },
            )}`}
        </p>
        <Button type="button" variant="ghost" size="sm" onClick={() => setEditing(true)}>
          {t('recordResp.edit')}
        </Button>
      </div>
      {rubric.model_answer && (
        <p className="mt-1 text-xs text-ink-500 line-clamp-2">
          <span className="font-semibold">{t('recordResp.modelAnswerLabel')}</span> {rubric.model_answer}
        </p>
      )}
    </div>
  );
};

/**
 * "Record a response" — the entry point that feeds the AI grading queue
 * (ASA-7b). The teacher picks a class, a student and one of their
 * short-answer questions, pastes the student's free-text answer, and the
 * server queues AI grading (202 → pending row in the queue below). Rubric
 * authoring lives right here because the rubric is what makes the AI's
 * suggestion fair — the form nudges the teacher to add one before grading.
 */
export const RecordResponsePanel = () => {
  const t = useT();
  const [isExpanded, setIsExpanded] = useState(false);
  const [roomId, setRoomId] = useState<number | null>(null);
  const [studentId, setStudentId] = useState<number | null>(null);
  const [subpartId, setSubpartId] = useState<number | null>(null);
  const [responseText, setResponseText] = useState('');

  const { data: rooms } = useSubjectRooms();
  const { data: students, isLoading: studentsLoading } = useRoomStudents(roomId);
  const { data: subparts, isLoading: subpartsLoading } = useShortAnswerSubparts(isExpanded);
  const submit = useSubmitOpenResponse();

  const canSubmit =
    roomId != null && studentId != null && subpartId != null && responseText.trim().length > 0;

  return (
    <div className="os-card p-4 sm:p-5">
      <button
        type="button"
        onClick={() => setIsExpanded((v) => !v)}
        aria-expanded={isExpanded}
        className="flex w-full items-center gap-1.5 text-left text-sm font-semibold text-ink-700 hover:text-ink-900 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500 rounded"
      >
        <span>{t('recordResp.recordForAI')}</span>
        <span className={`ml-auto transition-transform ${isExpanded ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isExpanded && (
        <form
          className="mt-3 space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSubmit) return;
            submit.mutate(
              {
                subject_room_id: roomId,
                student_id: studentId,
                subpart_id: subpartId,
                response_text: responseText.trim(),
              },
              { onSuccess: () => setResponseText('') }
            );
          }}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs text-ink-600">
              {t('recordResp.class')}
              <select
                value={roomId == null ? '' : String(roomId)}
                onChange={(e) => {
                  setRoomId(e.target.value ? Number(e.target.value) : null);
                  setStudentId(null);
                }}
                className="input-brand mt-1 block w-full text-sm"
              >
                <option value="">{t('recordResp.pickClass')}</option>
                {(rooms ?? []).map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.subject_name} · {r.classroom_display}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs text-ink-600">
              {t('recordResp.student')}
              <select
                value={studentId == null ? '' : String(studentId)}
                onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : null)}
                disabled={roomId == null || studentsLoading}
                className="input-brand mt-1 block w-full text-sm disabled:opacity-60"
              >
                <option value="">
                  {roomId == null
                    ? t('recordResp.pickClassFirst')
                    : studentsLoading
                      ? t('recordResp.loadingStudents')
                      : t('recordResp.pickStudent')}
                </option>
                {(students ?? []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name || s.username}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="block text-xs text-ink-600">
            {t('recordResp.shortAnswerQuestion')}
            <select
              value={subpartId == null ? '' : String(subpartId)}
              onChange={(e) => setSubpartId(e.target.value ? Number(e.target.value) : null)}
              disabled={subpartsLoading}
              className="input-brand mt-1 block w-full text-sm disabled:opacity-60"
            >
              <option value="">
                {subpartsLoading ? t('recordResp.loadingQuestions') : t('recordResp.pickQuestion')}
              </option>
              {(subparts ?? []).map((sp) => (
                <option key={sp.subpartId} value={sp.subpartId}>
                  {sp.label}
                </option>
              ))}
            </select>
          </label>
          {!subpartsLoading && (subparts ?? []).length === 0 && (
            <p className="text-xs text-ink-500">
              {t('recordResp.noShortAnswer')}
            </p>
          )}

          {subpartId != null && <RubricSection subpartId={subpartId} />}

          <label className="block text-xs text-ink-600">
            {t('recordResp.studentAnswer')}
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              rows={3}
              className="input-brand mt-1 block w-full text-sm"
              placeholder={t('recordResp.studentAnswerPlaceholder')}
            />
          </label>

          {submit.isError && (
            <p className="text-xs text-rose-600">
              {t('recordResp.queueError')}
            </p>
          )}
          {submit.isSuccess && (
            <p className="text-xs text-emerald-700" role="status">
              {t('recordResp.queuedSuccess')}
            </p>
          )}

          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-ink-400">{t('recordResp.aiSuggestsNote')}</p>
            <Button type="submit" variant="brand" size="sm" disabled={!canSubmit || submit.isPending}>
              {submit.isPending ? t('recordResp.queuing') : t('recordResp.sendToAI')}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
};
