import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { QuestionPreviewPanel } from './QuestionPreviewPanel';
import type { Question } from '@/types/index';

// RichContent renders HTML/LaTeX; we only assert chrome here.
const makeQuestion = (): Question =>
  ({
    id: 100,
    question_type: 'numeric',
    difficulty: 3,
    subject: 1,
    subject_name: 'Mathematics',
    chapter: 10,
    chapter_name: 'Algebra',
    standard: 8,
    tags: [],
    stem_text: '',
    subparts: [
      { id: 1, question_text: 'What is 2 + 2?', options: [], subpart_type: 'numeric', image_url: null },
    ],
  }) as unknown as Question;

describe('<QuestionPreviewPanel />', () => {
  it('shows the localized empty state when no question is selected (English default)', () => {
    render(<QuestionPreviewPanel question={null} />);
    expect(screen.getByText('Pick a question to preview')).toBeInTheDocument();
  });

  it('renders the question-type badge in Hindi when the locale is हिं', async () => {
    render(
      <I18nProvider initialLocale="hi">
        <QuestionPreviewPanel question={makeQuestion()} />
      </I18nProvider>,
    );
    // संख्यात्मक = "numeric" question type per the Glossary register.
    await waitFor(() => {
      expect(screen.getByText('संख्यात्मक')).toBeInTheDocument();
    });
  });
});
