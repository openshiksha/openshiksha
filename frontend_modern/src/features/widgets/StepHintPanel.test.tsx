/**
 * GSV-4 — tests for the host-side AI wrong-step coach.
 *
 * The panel never decides correctness: it renders whatever `verdict` the
 * deterministic backend returns. These tests pin the on-screen contract for
 * every branch — a real AI explanation (✨ AI-generated), the deterministic
 * static-hint fallback (neutral Auto-explanation + "AI unavailable" line), a
 * correct step (no AI, green note), an unparseable line, plus pending/error/
 * disabled states — and the grounded call shape.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { StepHintResponse } from './useStepHint';
import { StepHintPanel } from './StepHintPanel';

/**
 * Stub the GSV-3 hook so the panel never reaches into react-query (these tests
 * render it without a QueryClientProvider). Tests drive each branch by setting
 * `stepHintMock.data` / `isPending` / `isError`.
 */
const stepHintMock = vi.hoisted(() => ({
  mutate: vi.fn(),
  reset: vi.fn(),
  isPending: false,
  isError: false,
  data: undefined as StepHintResponse | undefined,
}));

vi.mock('./useStepHint', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./useStepHint')>();
  return { ...actual, useStepHint: () => stepHintMock };
});

beforeEach(() => {
  stepHintMock.mutate = vi.fn();
  stepHintMock.reset = vi.fn();
  stepHintMock.isPending = false;
  stepHintMock.isError = false;
  stepHintMock.data = undefined;
});

describe('StepHintPanel', () => {
  it('disables the ask button and prompts when a line is missing', () => {
    render(<StepHintPanel previous="2x + 3 = 7" current="   " />);
    expect(screen.getByRole('button', { name: /why is this wrong/i })).toBeDisabled();
    expect(screen.getByText(/enter a previous line and the new line/i)).toBeInTheDocument();
  });

  it('asks the endpoint with the trimmed line pair on click (grounded)', () => {
    render(<StepHintPanel previous="  2x + 3 = 7 " current=" 2x = 10 " />);
    fireEvent.click(screen.getByRole('button', { name: /why is this wrong/i }));
    expect(stepHintMock.mutate).toHaveBeenCalledWith({
      previous: '2x + 3 = 7',
      current: '2x = 10',
    });
  });

  it('shows the ✨ AI-generated badge + the AI explanation for a real wrong step', () => {
    stepHintMock.data = {
      verdict: 'wrong',
      reason: 'These equations have different solutions.',
      hint: 'You took 3 off the left but not the right — subtract it from both sides.',
      model_used: 'claude-sonnet-4-6',
      ai_available: true,
    };
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = 10" />);

    expect(screen.getByText('✨ AI-generated')).toBeInTheDocument();
    expect(screen.getByText(/subtract it from both sides/i)).toBeInTheDocument();
    expect(screen.getByText(/different solutions/i)).toBeInTheDocument();
    // The deterministic engine's verdict is what is shown — never an AI re-judge.
    expect(screen.getByText(/this changes the answer/i)).toBeInTheDocument();
    // No "AI unavailable" line on the real path.
    expect(screen.queryByText(/ai coach is unavailable/i)).not.toBeInTheDocument();
  });

  it('shows the neutral Auto-explanation badge + AI-unavailable line on the stub fallback', () => {
    stepHintMock.data = {
      verdict: 'wrong',
      reason: 'These equations have different solutions.',
      hint: 'Re-check this line term by term, and watch the signs.',
      model_used: 'stub',
      ai_available: false,
    };
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = 10" />);

    expect(screen.getByText('Auto-explanation')).toBeInTheDocument();
    expect(screen.queryByText('✨ AI-generated')).not.toBeInTheDocument();
    expect(screen.getByText(/watch the signs/i)).toBeInTheDocument();
    expect(screen.getByText(/ai coach is unavailable/i)).toBeInTheDocument();
  });

  it('shows a green "looks right" note for a correct step and never an AI badge', () => {
    stepHintMock.data = {
      verdict: 'correct',
      reason: 'Same solution as the line above.',
      hint: null,
      model_used: null,
      ai_available: false,
    };
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = 4" />);

    expect(screen.getByText(/this step looks right/i)).toBeInTheDocument();
    expect(screen.getByText(/same solution as the line above/i)).toBeInTheDocument();
    expect(screen.queryByText('✨ AI-generated')).not.toBeInTheDocument();
    expect(screen.queryByText('Auto-explanation')).not.toBeInTheDocument();
  });

  it('shows a neutral "could not check" note for an unparseable line (no AI)', () => {
    stepHintMock.data = {
      verdict: 'unparseable',
      reason: 'Could not read this line.',
      hint: null,
      model_used: null,
      ai_available: false,
    };
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = )(" />);

    expect(screen.getByText(/couldn't check this line/i)).toBeInTheDocument();
    expect(screen.queryByText('✨ AI-generated')).not.toBeInTheDocument();
  });

  it('shows a pending state while the coach is thinking', () => {
    stepHintMock.isPending = true;
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = 10" />);
    expect(screen.getByText(/asking the coach/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /checking/i })).toBeDisabled();
  });

  it('shows a friendly error when the request fails', () => {
    stepHintMock.isError = true;
    render(<StepHintPanel previous="2x + 3 = 7" current="2x = 10" />);
    expect(screen.getByText(/couldn't reach the step coach/i)).toBeInTheDocument();
  });
});
