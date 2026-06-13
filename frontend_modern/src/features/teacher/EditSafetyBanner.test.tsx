import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { I18nProvider } from '@/shared/i18n';
import { EditSafetyBanner } from './EditSafetyBanner';

describe('<EditSafetyBanner />', () => {
  it('renders nothing when not yet used in any assignment', () => {
    const { container } = render(
      <EditSafetyBanner assignedCount={0} hasGradedSubmissions={false} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders the singular form for one assignment', () => {
    render(
      <EditSafetyBanner
        assignedCount={1}
        hasGradedSubmissions={false}
        subject="question"
      />,
    );
    expect(screen.getByTestId('edit-safety-banner')).toBeInTheDocument();
    expect(screen.getByText(/used in 1 assignment\./i)).toBeInTheDocument();
    // No "graded against" wording when nothing is graded yet.
    expect(screen.queryByText(/graded against/i)).not.toBeInTheDocument();
  });

  it('renders the plural form and the graded wording when applicable', () => {
    render(
      <EditSafetyBanner
        assignedCount={3}
        hasGradedSubmissions
        subject="problemSet"
      />,
    );
    expect(screen.getByText(/used in 3 assignments\./i)).toBeInTheDocument();
    expect(screen.getByText(/graded against/i)).toBeInTheDocument();
    // First letter of the noun is capitalised in the headline.
    expect(screen.getByText(/^This problem set/)).toBeInTheDocument();
  });

  it('renders the Hindi headline when the locale is हिं', async () => {
    render(
      <I18nProvider initialLocale="hi">
        <EditSafetyBanner assignedCount={2} hasGradedSubmissions={false} subject="problemSet" />
      </I18nProvider>,
    );
    // Hindi dict loads via dynamic import — strings swap once it arrives.
    // समस्या सेट = "problem set" per the Glossary register.
    await waitFor(() => {
      expect(screen.getByText(/समस्या सेट/)).toBeInTheDocument();
    });
  });

  it('never disables anything (informational only)', () => {
    render(<EditSafetyBanner assignedCount={5} hasGradedSubmissions />);
    const banner = screen.getByTestId('edit-safety-banner');
    // The banner itself must not render any disabled control — AIV-1/2 make
    // editing safe, so this is purely advisory.
    expect(banner.querySelectorAll('[disabled]').length).toBe(0);
    expect(banner.querySelectorAll('button').length).toBe(0);
  });
});
