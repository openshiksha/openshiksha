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

  it('seeds custom-html with a rich sandbox demo', () => {
    renderPage('/widgets/dev?kind=custom-html');

    const config = screen.getByLabelText(/config json/i) as HTMLTextAreaElement;
    expect(config.value).toContain('Sandboxed HTML can still feel alive');
    expect(config.value).toContain('energy');
    expect(screen.getByTestId('widget-preview')).toHaveTextContent('custom-html');
  });
});
