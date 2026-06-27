import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { WidgetDevPage } from './WidgetDevPage';

vi.mock('@/shared/ui/InteractiveWidget', () => ({
  InteractiveWidget: ({ kind, config, variables }: {
    kind?: string;
    config?: Record<string, unknown>;
    variables?: Record<string, unknown>;
  }) => (
    <div data-testid="widget-preview">
      {kind}::{JSON.stringify(config)}::{JSON.stringify(variables)}
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

  it('shows the wrong-step AI coach (with a seeded line pair) only for step-solver', () => {
    renderPage('/widgets/dev?kind=number-line');
    expect(screen.queryByTestId('step-coach')).not.toBeInTheDocument();

    renderPage('/widgets/dev?kind=step-solver');
    expect(screen.getByRole('heading', { name: /wrong-step explainer/i })).toBeInTheDocument();
    expect(screen.getByTestId('step-coach')).toHaveTextContent('2x + 3 = 7::2x = 10');
  });

  it('seeds custom-html with a rich sandbox demo', () => {
    renderPage('/widgets/dev?kind=custom-html');

    const config = screen.getByLabelText(/config json/i) as HTMLTextAreaElement;
    expect(config.value).toContain('Sandboxed HTML can still feel alive');
    expect(config.value).toContain('energy');
    expect(screen.getByTestId('widget-preview')).toHaveTextContent('custom-html');
  });
});
