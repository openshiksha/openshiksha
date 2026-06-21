import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { UpdateBanner } from './UpdateBanner';
import { I18nProvider } from '@/shared/i18n/I18nProvider';

const renderBanner = (onRefresh = vi.fn()) => {
  render(
    <I18nProvider initialLocale="en">
      <UpdateBanner onRefresh={onRefresh} />
    </I18nProvider>,
  );
  return onRefresh;
};

describe('<UpdateBanner />', () => {
  it('announces a new version with a polite status role', () => {
    renderBanner();
    const banner = screen.getByRole('status');
    expect(banner).toHaveAttribute('aria-live', 'polite');
    expect(banner).toHaveTextContent(/new version/i);
  });

  it('calls onRefresh when the refresh button is clicked', async () => {
    const onRefresh = renderBanner();
    await userEvent.click(screen.getByRole('button', { name: /refresh/i }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
