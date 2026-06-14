import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { I18nProvider, useI18n, resolveInitialLocale, LOCALE_STORAGE_KEY } from './index';
import { useT } from './useT';
import { LanguageSwitcher } from './LanguageSwitcher';
import { en } from './locales/en';
import { hi } from './locales/hi';
import { mr } from './locales/mr';

/** Tiny probe component exposing the i18n surface to assertions. */
const Probe = ({ vars }: { vars?: Record<string, string | number> }) => {
  const { locale, setLocale } = useI18n();
  const t = useT();
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="title">{t('login.title', vars)}</span>
      <span data-testid="interpolated">{t('common.languageSwitchTo', vars)}</span>
      <button onClick={() => setLocale('hi')}>to-hi</button>
      <button onClick={() => setLocale('en')}>to-en</button>
    </div>
  );
};

describe('i18n', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.lang = 'en';
  });

  it('serves English strings by default', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('locale').textContent).toBe('en');
    expect(screen.getByTestId('title').textContent).toBe(en['login.title']);
  });

  it('interpolates {var} placeholders and leaves unknown ones intact', () => {
    render(
      <I18nProvider>
        <Probe vars={{ language: 'English' }} />
      </I18nProvider>,
    );
    expect(screen.getByTestId('interpolated').textContent).toBe('Switch language to English');
  });

  it('switches to Hindi, persists the choice, and syncs <html lang>', async () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    fireEvent.click(screen.getByText('to-hi'));

    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('hi');
    expect(document.documentElement.lang).toBe('hi');

    // Hindi dict loads via dynamic import — strings swap once it arrives.
    await waitFor(() => {
      expect(screen.getByTestId('title').textContent).toBe(hi['login.title']);
    });
  });

  it('falls back to English while/if a Hindi string is unavailable', () => {
    // Before the dynamic import resolves, t() must serve English, not blank.
    render(
      <I18nProvider initialLocale="hi">
        <Probe />
      </I18nProvider>,
    );
    const text = screen.getByTestId('title').textContent;
    expect([en['login.title'], hi['login.title']]).toContain(text);
    expect(text).not.toBe('');
  });

  it('seeds the locale from profileLocale when no device override exists', async () => {
    render(
      <I18nProvider profileLocale="hi">
        <Probe />
      </I18nProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId('locale').textContent).toBe('hi');
    });
    // Seeding is not an explicit device choice — localStorage stays untouched.
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBeNull();
  });

  it('the device override wins over profileLocale', () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'en');
    render(
      <I18nProvider profileLocale="hi">
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('locale').textContent).toBe('en');
  });

  it('fires onLocaleChange on explicit switches, not on seeding', async () => {
    const onLocaleChange = vi.fn();
    render(
      <I18nProvider profileLocale="hi" onLocaleChange={onLocaleChange}>
        <Probe />
      </I18nProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId('locale').textContent).toBe('hi');
    });
    expect(onLocaleChange).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText('to-en'));
    expect(onLocaleChange).toHaveBeenCalledWith('en');
  });

  it('resolveInitialLocale honors the localStorage device override', () => {
    expect(resolveInitialLocale()).toBe('en');
    localStorage.setItem(LOCALE_STORAGE_KEY, 'hi');
    expect(resolveInitialLocale()).toBe('hi');
    localStorage.setItem(LOCALE_STORAGE_KEY, 'fr'); // unsupported → default
    expect(resolveInitialLocale()).toBe('en');
  });

  it('works without a provider as an English-only fallback', () => {
    render(<Probe vars={{ language: 'English' }} />);
    expect(screen.getByTestId('locale').textContent).toBe('en');
    expect(screen.getByTestId('title').textContent).toBe(en['login.title']);
  });

  describe('Marathi pilot (LA-9b)', () => {
    it('renders Marathi anonymous-journey strings when active', async () => {
      render(
        <I18nProvider initialLocale="mr">
          <Probe />
        </I18nProvider>,
      );
      await waitFor(() => {
        expect(screen.getByTestId('title').textContent).toBe(mr['login.title']);
      });
      // Pilot subset: a translated key resolves to Marathi…
      expect(screen.getByTestId('locale').textContent).toBe('mr');
    });

    it('falls back to English for keys the pilot does not define yet', () => {
      // The teacher surface is outside the Marathi pilot, so its keys must
      // resolve to English, never a blank (principle 3).
      const NotYetTranslated = () => {
        const t = useT();
        return <span data-testid="fallback">{t('teacher.title')}</span>;
      };
      render(
        <I18nProvider initialLocale="mr">
          <NotYetTranslated />
        </I18nProvider>,
      );
      expect(screen.getByTestId('fallback').textContent).toBe(en['teacher.title']);
    });

    it('renders Marathi student-loop chrome (LA-9c)', async () => {
      const StudentChrome = () => {
        const t = useT();
        return <span data-testid="dash">{t('dashboard.title')}</span>;
      };
      render(
        <I18nProvider initialLocale="mr">
          <StudentChrome />
        </I18nProvider>,
      );
      await waitFor(() => {
        expect(screen.getByTestId('dash').textContent).toBe(mr['dashboard.title']);
      });
      expect(screen.getByTestId('dash').textContent).not.toBe(en['dashboard.title']);
    });

    it('syncs <html lang="mr"> when Marathi is selected', () => {
      render(
        <I18nProvider initialLocale="mr">
          <Probe />
        </I18nProvider>,
      );
      expect(document.documentElement.lang).toBe('mr');
    });
  });

  describe('LanguageSwitcher', () => {
    it('renders one button per registered locale (EN | हिं | मरा)', () => {
      render(
        <I18nProvider>
          <LanguageSwitcher />
        </I18nProvider>,
      );
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(3);
      expect(buttons.map((b) => b.textContent)).toEqual(['EN', 'हिं', 'मरा']);
    });

    it('toggles the locale with aria-pressed state', async () => {
      render(
        <I18nProvider>
          <LanguageSwitcher />
          <Probe />
        </I18nProvider>,
      );
      const enButton = screen.getByRole('button', { name: /switch language to english/i });
      const hiButton = screen.getByRole('button', { name: /हिंदी/ });

      expect(enButton.getAttribute('aria-pressed')).toBe('true');
      expect(hiButton.getAttribute('aria-pressed')).toBe('false');

      fireEvent.click(hiButton);
      await waitFor(() => {
        expect(hiButton.getAttribute('aria-pressed')).toBe('true');
      });
      expect(screen.getByTestId('locale').textContent).toBe('hi');
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('hi');
    });

    it('selects Marathi from the switcher', async () => {
      render(
        <I18nProvider>
          <LanguageSwitcher />
          <Probe />
        </I18nProvider>,
      );
      fireEvent.click(screen.getByRole('button', { name: /मराठी/ }));
      await waitFor(() => {
        expect(screen.getByTestId('locale').textContent).toBe('mr');
      });
      expect(document.documentElement.lang).toBe('mr');
      expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('mr');
    });
  });
});
