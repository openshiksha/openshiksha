/**
 * PV-3 — tests for the on-screen AI practice-problem generator.
 *
 * The panel never decides correctness: it renders whatever verified
 * `{widget_config, correct_answer}` the backend returns (PV-1 gates every
 * proposal server-side). These tests pin the on-screen contract for every
 * branch — a real verified proposal (✨ AI-generated + the answer shown), a
 * snap-repaired proposal (the "Answer adjusted to the grid" flag), the
 * deterministic safe-default fallback (neutral Auto-problem + "AI unavailable"
 * line), the PV-5b randomize toggle (`allow_variables` on the call; the
 * `🎲 Randomized per student` pill + validated ranges only on a verified
 * `ok_variable` response), plus pending/error/disabled states and the topic
 * call shape.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { PracticeProblemResponse } from './usePracticeProblem';
import { PracticeProblemPanel } from './PracticeProblemPanel';

/** Stub the InteractiveWidget iframe — the panel test asserts the PV-3 chrome
 *  (badges/answer/fallback), not sandbox rendering (covered elsewhere). */
vi.mock('@/shared/ui/InteractiveWidget', () => ({
  InteractiveWidget: ({ kind }: { kind: string }) => (
    <div data-testid="interactive-widget" data-kind={kind} />
  ),
}));

/**
 * Stub the PV-2 hook so the panel never reaches into react-query (these tests
 * render it without a QueryClientProvider). Tests drive each branch by setting
 * `proposalMock.data` / `isPending` / `isError`.
 */
const proposalMock = vi.hoisted(() => ({
  mutate: vi.fn(),
  isPending: false,
  isError: false,
  data: undefined as PracticeProblemResponse | undefined,
}));

vi.mock('./usePracticeProblem', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./usePracticeProblem')>();
  return { ...actual, usePracticeProblem: () => proposalMock };
});

beforeEach(() => {
  proposalMock.mutate = vi.fn();
  proposalMock.isPending = false;
  proposalMock.isError = false;
  proposalMock.data = undefined;
});

const realProposal: PracticeProblemResponse = {
  widget_kind: 'number-line',
  widget_config: { min: 0, max: 1, step: 0.5 },
  correct_answer: { answer: 0.5 },
  model_used: 'claude-sonnet-4-6',
  ai_available: true,
  repaired: false,
  verdict_code: 'ok',
  variable_constraints: {},
};

describe('PracticeProblemPanel', () => {
  it('calls the endpoint with the trimmed topic on click (randomisation off by default)', () => {
    render(<PracticeProblemPanel />);
    const input = screen.getByLabelText(/topic/i);
    fireEvent.change(input, { target: { value: '  mark 3/4 on a number line  ' } });
    fireEvent.click(screen.getByRole('button', { name: /generate & verify/i }));
    expect(proposalMock.mutate).toHaveBeenCalledWith({
      topic: 'mark 3/4 on a number line',
      allow_variables: false,
    });
  });

  it('sets allow_variables when the randomize toggle is checked (PV-5b)', () => {
    render(<PracticeProblemPanel />);
    fireEvent.click(screen.getByLabelText(/each student gets a different value/i));
    fireEvent.click(screen.getByRole('button', { name: /generate & verify/i }));
    expect(proposalMock.mutate).toHaveBeenCalledWith(
      expect.objectContaining({ allow_variables: true }),
    );
  });

  it('disables the button for an empty topic', () => {
    render(<PracticeProblemPanel />);
    const input = screen.getByLabelText(/topic/i);
    fireEvent.change(input, { target: { value: '   ' } });
    expect(screen.getByRole('button', { name: /generate & verify/i })).toBeDisabled();
  });

  it('renders a real verified proposal: ✨ badge, verified pill, preview, and the answer', () => {
    proposalMock.data = realProposal;
    render(<PracticeProblemPanel />);

    expect(screen.getByText('✨ AI-generated')).toBeInTheDocument();
    expect(screen.getByText(/verified answerable/i)).toBeInTheDocument();
    // The verified config renders in the live sandbox preview.
    const widget = screen.getByTestId('interactive-widget');
    expect(widget).toHaveAttribute('data-kind', 'number-line');
    // The answer is shown on screen.
    expect(screen.getByText('0.5')).toBeInTheDocument();
    // No fallback line, no "adjusted" flag, and no randomized pill on the
    // clean static real path.
    expect(screen.queryByText(/ai proposer is unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/adjusted to the grid/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/randomized per student/i)).not.toBeInTheDocument();
  });

  it('shows the 🎲 pill, the expression answer, and the validated ranges for a randomized proposal (PV-5b)', () => {
    proposalMock.data = {
      ...realProposal,
      widget_config: { min: 0, max: 10, step: 1 },
      correct_answer: { answer: '{{a}}' },
      verdict_code: 'ok_variable',
      variable_constraints: { a: { min: 1, max: 9, integer: true } },
    };
    render(<PracticeProblemPanel />);

    expect(screen.getByText('✨ AI-generated')).toBeInTheDocument();
    expect(screen.getByText(/verified answerable/i)).toBeInTheDocument();
    expect(screen.getByText('🎲 Randomized per student')).toBeInTheDocument();
    // The answer is shown as the per-student expression…
    expect(screen.getByText('{{a}}')).toBeInTheDocument();
    // …with its validated, reachable-for-all sampling range on screen.
    expect(screen.getByText('{{a}}: 1 to 9 (whole numbers)')).toBeInTheDocument();
    expect(
      screen.getByText(/sampled them all and confirmed every one is reachable/i),
    ).toBeInTheDocument();
  });

  it('flags a snap-repaired real proposal ("Answer adjusted to the grid")', () => {
    proposalMock.data = {
      ...realProposal,
      widget_config: { min: 0, max: 1, step: 0.25 },
      correct_answer: { answer: 0.8 },
      repaired: true,
    };
    render(<PracticeProblemPanel />);

    expect(screen.getByText('✨ AI-generated')).toBeInTheDocument();
    expect(screen.getByText(/adjusted to the grid/i)).toBeInTheDocument();
    expect(screen.getByText('0.8')).toBeInTheDocument();
  });

  it('shows the neutral Auto-problem badge + AI-unavailable line on the safe-default fallback', () => {
    proposalMock.data = {
      ...realProposal,
      model_used: 'stub',
      ai_available: false,
      verdict_code: 'safe_default',
    };
    render(<PracticeProblemPanel />);

    expect(screen.getByText('Auto-problem')).toBeInTheDocument();
    expect(screen.queryByText('✨ AI-generated')).not.toBeInTheDocument();
    // Still verified — the safe default is PV-1-passed by construction.
    expect(screen.getByText(/verified answerable/i)).toBeInTheDocument();
    expect(screen.getByText(/ai proposer is unavailable/i)).toBeInTheDocument();
    // A safe default is never labelled as a repaired real generation, and it
    // is never randomized (the backend always ships it static).
    expect(screen.queryByText(/adjusted to the grid/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/randomized per student/i)).not.toBeInTheDocument();
  });

  it('shows a pending state while generating', () => {
    proposalMock.isPending = true;
    render(<PracticeProblemPanel />);
    expect(screen.getByText(/verifying it's answerable/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generating/i })).toBeDisabled();
  });

  it('shows a friendly error when the request fails', () => {
    proposalMock.isError = true;
    render(<PracticeProblemPanel />);
    expect(screen.getByText(/couldn't reach the problem generator/i)).toBeInTheDocument();
  });
});
