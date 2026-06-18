import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { PushBanner } from './PushBanner';
import { I18nProvider } from '@/shared/i18n/I18nProvider';
import * as hook from './usePushSubscription';

const renderBanner = () =>
  render(
    <I18nProvider initialLocale="en">
      <PushBanner />
    </I18nProvider>,
  );

const state = (over: Partial<hook.PushSubscriptionState> = {}): hook.PushSubscriptionState => ({
  supported: true,
  permission: 'default',
  isSubscribed: false,
  busy: false,
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
  ...over,
});

beforeEach(() => localStorage.clear());
afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('<PushBanner /> (MPN-4)', () => {
  it('renders the enable prompt when push is supported and not subscribed', () => {
    vi.spyOn(hook, 'usePushSubscription').mockReturnValue(state());
    renderBanner();
    expect(screen.getByText(/get reminders on your phone/i)).toBeInTheDocument();
  });

  it('hides when push is unsupported', () => {
    vi.spyOn(hook, 'usePushSubscription').mockReturnValue(state({ supported: false }));
    const { container } = renderBanner();
    expect(container.firstChild).toBeNull();
  });

  it('hides when already subscribed', () => {
    vi.spyOn(hook, 'usePushSubscription').mockReturnValue(state({ isSubscribed: true }));
    const { container } = renderBanner();
    expect(container.firstChild).toBeNull();
  });

  it('hides when permission is denied', () => {
    vi.spyOn(hook, 'usePushSubscription').mockReturnValue(state({ permission: 'denied' }));
    const { container } = renderBanner();
    expect(container.firstChild).toBeNull();
  });
});
