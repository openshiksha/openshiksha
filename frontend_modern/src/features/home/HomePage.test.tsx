import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { I18nProvider, type Locale } from '@/shared/i18n';
import { HomePage } from './HomePage';

function renderHome(locale: Locale = 'en') {
  return render(
    <I18nProvider initialLocale={locale}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </I18nProvider>,
  );
}

describe('HomePage', () => {
  it('renders the hero, pillars, and CTAs in English by default', () => {
    renderHome();
    expect(screen.getByText('Unlock every child’s potential.')).toBeDefined();
    expect(screen.getByText('Practice')).toBeDefined();
    expect(screen.getByText('Evaluate')).toBeDefined();
    expect(screen.getByText('Analyse')).toBeDefined();
    expect(screen.getByText('Start free as a student')).toBeDefined();
  });

  it('renders entirely in Hindi when the locale is hi', async () => {
    renderHome('hi');
    // Hindi dictionary loads via dynamic import — wait for the swap.
    await waitFor(() => expect(screen.getByText('हर बच्चे की क्षमता को खोलिए।')).toBeDefined());
    expect(screen.getByText('अभ्यास')).toBeDefined();
    expect(screen.getByText('जाँच')).toBeDefined();
    expect(screen.getByText('विश्लेषण')).toBeDefined();
    expect(screen.getByText('मुख्य विशेषताएँ')).toBeDefined();
    expect(screen.getByText('अभी शुरू करें')).toBeDefined();
    expect(screen.getByText('विद्यार्थी के रूप में मुफ़्त शुरू करें')).toBeDefined();
  });
});
