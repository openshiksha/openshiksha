import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { WidgetDevPage } from './WidgetDevPage';

type StepArg = { previous: string; current: string; verdict: 'ok' | 'bad' | 'neutral'; reason: string };

vi.mock('@/shared/ui/InteractiveWidget', () => ({
  InteractiveWidget: ({ kind, config, variables, onStep }: {
    kind?: string;
    config?: Record<string, unknown>;
    variables?: Record<string, unknown>;
    onStep?: (step: StepArg) => void;
  }) => (
    <div data-testid="widget-preview">
      {kind}::{JSON.stringify(config)}::{JSON.stringify(variables)}
      {/* Buttons let a test simulate the widget committing a step (GSV-4b). */}
      <button
        type="button"
        onClick={() =>
          onStep?.({ previous: 'x + 5 = 9', current: 'x = 5', verdict: 'bad', reason: 'changes solution' })
        }
      >
        emit-bad-step
      </button>
      <button
        type="button"
        onClick={() =>
          onStep?.({ previous: 'x + 5 = 9', current: 'x = 4', verdict: 'ok', reason: 'ok' })
        }
      >
        emit-ok-step
      </button>
    </div>
  ),
}));

// GSV-4 — stub the step coach so the dev-page tests don't need a
// QueryClientProvider; its own behaviour is covered by StepHintPanel.test.tsx.
// Echo the props so we can assert the dev page wires the line pair through.
vi.mock('./StepHintPanel', () => ({
  StepHintPanel: ({ previous, current }: { previous: string; current: string }) => (
    <div data-testid="step-coach">{previous}::{current}</div>
  ),
}));

// PV-3 — stub the practice-problem generator so the dev-page tests don't need a
// QueryClientProvider; its own behaviour is covered by PracticeProblemPanel.test.tsx.
vi.mock('./PracticeProblemPanel', () => ({
  PracticeProblemPanel: () => <div data-testid="practice-problem-panel" />,
}));

function renderPage(route = '/widgets/dev') {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <WidgetDevPage />
    </MemoryRouter>,
  );
}

describe('<WidgetDevPage />', () => {
  it('loads a widget kind from the query string and seeds config defaults from schema', () => {
    renderPage('/widgets/dev?kind=fraction-bar');

    expect(screen.getByRole('heading', { name: /widget dev playground/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/widget kind/i)).toHaveValue('fraction-bar');
    expect(screen.getByTestId('widget-preview')).toHaveTextContent('fraction-bar');
    expect((screen.getByLabelText(/config json/i) as HTMLTextAreaElement).value).toContain('"denominator": 4');
  });

  it('blocks preview while the config editor contains invalid JSON', async () => {
    const user = userEvent.setup();
    renderPage('/widgets/dev?kind=number-line');

    const config = screen.getByLabelText(/config json/i);
    await user.clear(config);
    await user.paste('{ nope');

    expect(screen.getByText(/fix the json error/i)).toBeInTheDocument();
    expect(screen.queryByTestId('widget-preview')).not.toBeInTheDocument();
  });

  it('always wires in the PV-3 practice-problem generator (independent of the preview kind)', () => {
    renderPage('/widgets/dev?kind=number-line');
    expect(screen.getByTestId('practice-problem-panel')).toBeInTheDocument();
  });

  it('shows the wrong-step AI coach (with a seeded line pair) only for step-solver', () => {
    renderPage('/widgets/dev?kind=number-line');
    expect(screen.queryByTestId('step-coach')).not.toBeInTheDocument();

    renderPage('/widgets/dev?kind=step-solver');
    expect(screen.getByRole('heading', { name: /wrong-step explainer/i })).toBeInTheDocument();
    expect(screen.getByTestId('step-coach')).toHaveTextContent('2x + 3 = 7::2x = 10');
  });

  it('auto-feeds a wrong step from the widget into the coach (GSV-4b) and flags the source', async () => {
    const user = userEvent.setup();
    renderPage('/widgets/dev?kind=step-solver');

    // Seeded manual pair before any widget interaction; no auto-filled flag yet.
    expect(screen.getByTestId('step-coach')).toHaveTextContent('2x + 3 = 7::2x = 10');
    expect(screen.queryByText(/auto-filled from your last wrong step/i)).not.toBeInTheDocument();

    // The widget commits a WRONG step → the coach pair updates to that exact
    // pair and the auto-filled affordance appears.
    await user.click(screen.getByRole('button', { name: 'emit-bad-step' }));
    expect(screen.getByTestId('step-coach')).toHaveTextContent('x + 5 = 9::x = 5');
    expect(screen.getByText(/auto-filled from your last wrong step/i)).toBeInTheDocument();
  });

  it('does NOT auto-feed a correct step — the AI coach only ever sees wrong steps', async () => {
    const user = userEvent.setup();
    renderPage('/widgets/dev?kind=step-solver');

    await user.click(screen.getByRole('button', { name: 'emit-ok-step' }));
    // Pair unchanged from the seed; no auto-filled flag.
    expect(screen.getByTestId('step-coach')).toHaveTextContent('2x + 3 = 7::2x = 10');
    expect(screen.queryByText(/auto-filled from your last wrong step/i)).not.toBeInTheDocument();
  });

  it('typing in the coach inputs clears the auto-filled flag (back to manual)', async () => {
    const user = userEvent.setup();
    renderPage('/widgets/dev?kind=step-solver');

    await user.click(screen.getByRole('button', { name: 'emit-bad-step' }));
    expect(screen.getByText(/auto-filled from your last wrong step/i)).toBeInTheDocument();

    const prevInput = screen.getByLabelText(/previous line/i);
    await user.type(prevInput, '!');
    expect(screen.queryByText(/auto-filled from your last wrong step/i)).not.toBeInTheDocument();
  });

  it('seeds custom-html with a rich sandbox demo', () => {
    renderPage('/widgets/dev?kind=custom-html');

    const config = screen.getByLabelText(/config json/i) as HTMLTextAreaElement;
    expect(config.value).toContain('Sandboxed HTML can still feel alive');
    expect(config.value).toContain('energy');
    expect(screen.getByTestId('widget-preview')).toHaveTextContent('custom-html');
  });
});
