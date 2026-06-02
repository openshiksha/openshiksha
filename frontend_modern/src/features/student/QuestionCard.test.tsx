import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import { QuestionCard } from './QuestionCard';
import type { Question, QuestionSubpart, SubpartType } from '@/types/index';

// M7-03b: the subpart input widget must switch on `subpart.subpart_type`, not
// the (possibly `compound`) parent question type.

function makeSubpart(over: Partial<QuestionSubpart>): QuestionSubpart {
  return {
    id: 1,
    index: 0,
    tags: [],
    question_text: 'prompt',
    options: null,
    ...over,
  };
}

function renderCard(question: Question) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <QuestionCard
        question={question}
        questionNumber={1}
        answers={{}}
        onAnswerChange={() => {}}
        isSubmitted={false}
      />
    </QueryClientProvider>
  );
}

function compoundQuestion(subparts: QuestionSubpart[]): Question {
  return {
    id: 10,
    standard: 8,
    subject: 1,
    chapter: 1,
    question_type: 'compound',
    difficulty: 2,
    tags: [],
    subparts,
    is_active: true,
    created_at: '2026-06-01T00:00:00Z',
  };
}

describe('QuestionCard — per-subpart widget (M7-03b)', () => {
  it('renders an option list for an mcq subpart and a numeric input for a numeric subpart in one compound question', () => {
    const mcq = makeSubpart({
      id: 101,
      index: 0,
      subpart_type: 'mcq',
      options: [
        { key: 'A', text: 'seven' },
        { key: 'B', text: 'eight' },
      ],
    });
    const numeric = makeSubpart({ id: 102, index: 1, subpart_type: 'numeric', options: null });

    renderCard(compoundQuestion([mcq, numeric]));

    // mcq subpart → radio inputs keyed by subpart id
    const radios = screen.getAllByRole('radio');
    expect(radios).toHaveLength(2);
    expect(radios[0]).toHaveAttribute('name', 'subpart-101');

    // numeric subpart → a number input
    const numberInput = screen.getByRole('spinbutton');
    expect(numberInput).toHaveAttribute('type', 'number');
  });

  it('falls back to the parent question type when subpart_type is blank', () => {
    // Hand-authored legacy row: blank subpart_type, parent type drives the widget.
    const sp = makeSubpart({
      id: 201,
      subpart_type: '',
      options: [
        { key: 'A', text: 'x' },
        { key: 'B', text: 'y' },
      ],
    });
    const question: Question = {
      ...compoundQuestion([sp]),
      question_type: 'mcq' as SubpartType,
    };
    renderCard(question);
    expect(screen.getAllByRole('radio')).toHaveLength(2);
  });

  it('renders a multi_select subpart as checkboxes', () => {
    const sp = makeSubpart({
      id: 301,
      subpart_type: 'multi_select',
      options: [
        { key: 'A', text: 'a' },
        { key: 'B', text: 'b' },
      ],
    });
    renderCard(compoundQuestion([sp]));
    const boxes = screen.getAllByRole('checkbox');
    expect(boxes).toHaveLength(2);
  });

  it('renders a text input for a fill_blank subpart', () => {
    const sp = makeSubpart({ id: 401, subpart_type: 'fill_blank', options: null });
    const { container } = renderCard(compoundQuestion([sp]));
    const textInput = within(container).getByPlaceholderText('Enter your answer');
    expect(textInput).toHaveAttribute('type', 'text');
  });
});
