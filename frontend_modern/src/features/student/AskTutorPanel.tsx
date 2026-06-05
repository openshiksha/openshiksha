import { useRef, useState, type FormEvent } from 'react';
import type { TutorConversation, TutorMessage } from '@/types/index';
import { RichContent } from '@/shared/ui';
import { useStartTutor, useTutorMessage } from './useTutor';

/**
 * Student-facing AI Tutor chat, anchored to a single question subpart.
 *
 * Collapsed by default behind an "Ask the tutor" button so it never distracts
 * before the student wants help. The tutor is Socratic — it guides without
 * revealing the answer — so it stays available during practice (unlike the
 * worked solution, which only appears after grading).
 */
export function AskTutorPanel({ subpartId }: { subpartId: number }) {
  const [open, setOpen] = useState(false);
  const [conversation, setConversation] = useState<TutorConversation | null>(null);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const start = useStartTutor();
  const followUp = useTutorMessage();
  const isSending = start.isPending || followUp.isPending;
  const isError = start.isError || followUp.isError;

  const messages: TutorMessage[] = conversation?.messages ?? [];

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isSending) return;
    setInput('');

    const onSuccess = (data: TutorConversation) => {
      setConversation(data);
      requestAnimationFrame(() => inputRef.current?.focus());
    };

    if (conversation) {
      followUp.mutate({ conversationId: conversation.id, message: text }, { onSuccess });
    } else {
      start.mutate({ subpart_id: subpartId, message: text }, { onSuccess });
    }
  };

  if (!open) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={() => {
            setOpen(true);
            requestAnimationFrame(() => inputRef.current?.focus());
          }}
          className="text-xs font-medium text-brand-700 hover:text-brand-800 transition-colors motion-reduce:transition-none focus:outline-none focus-visible:underline"
        >
          🧑‍🏫 Ask the tutor
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50/60 p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-brand-700">
          AI Tutor
        </span>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="text-xs text-ink-400 hover:text-ink-600 focus:outline-none focus-visible:underline"
          aria-label="Hide tutor"
        >
          Hide
        </button>
      </div>

      {messages.length === 0 && !isSending && (
        <p className="mt-2 text-xs text-ink-500 leading-relaxed">
          Stuck? Ask me anything about this question. I&apos;ll help you think it through
          step by step — but I won&apos;t just give away the answer!
        </p>
      )}

      <div className="mt-2 space-y-2" aria-live="polite">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === 'student' ? 'flex justify-end' : 'flex justify-start'}
          >
            <div
              className={
                m.role === 'student'
                  ? 'max-w-[85%] rounded-lg rounded-br-sm bg-brand-600 px-3 py-2 text-sm text-white'
                  : 'max-w-[85%] rounded-lg rounded-bl-sm border border-brand-100 bg-white px-3 py-2 text-sm text-ink-800 leading-relaxed'
              }
            >
              {m.role === 'tutor' ? <RichContent text={m.content} variant="block" /> : m.content}
            </div>
          </div>
        ))}

        {isSending && <p className="text-xs text-ink-500">The tutor is thinking…</p>}

        {isError && (
          <p className="text-xs text-rose-600">
            The tutor is unavailable right now. Please try again in a moment.
          </p>
        )}
      </div>

      <form onSubmit={handleSend} className="mt-3 flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isSending}
          placeholder="Type your question…"
          aria-label="Message the tutor"
          className="input-brand flex-1 text-sm disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={isSending || input.trim().length === 0}
          className="btn-brand px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
