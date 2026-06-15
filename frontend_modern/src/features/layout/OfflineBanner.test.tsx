import { render, screen, act } from '@testing-library/react';
import { afterEach, describe, it, expect, vi } from 'vitest';
import { OfflineBanner } from './OfflineBanner';
import { I18nProvider } from '@/shared/i18n/I18nProvider';

const setOnLine = (value: boolean) => {
  Object.defineProperty(navigator, 'onLine', { configurable: true, value });
};

const renderBanner = () =>
  render(
    <I18nProvider initialLocale="en">
      <OfflineBanner />
    </I18nProvider>,
  );

afterEach(() => {
  setOnLine(true);
  vi.restoreAllMocks();
});

describe('<OfflineBanner />', () => {
  it('renders nothing when online', () => {
    setOnLine(true);
    const { container } = renderBanner();
    expect(container.firstChild).toBeNull();
  });

  it('shows a polite status banner when offline', () => {
    setOnLine(false);
    renderBanner();
    const banner = screen.getByRole('status');
    expect(banner).toHaveAttribute('aria-live', 'polite');
    expect(banner).toHaveTextContent(/offline/i);
  });

  it('appears and disappears as connectivity changes', () => {
    setOnLine(true);
    renderBanner();
    expect(screen.queryByRole('status')).toBeNull();

    act(() => {
      setOnLine(false);
      window.dispatchEvent(new Event('offline'));
    });
    expect(screen.getByRole('status')).toBeInTheDocument();

    act(() => {
      setOnLine(true);
      window.dispatchEvent(new Event('online'));
    });
    expect(screen.queryByRole('status')).toBeNull();
  });
});
