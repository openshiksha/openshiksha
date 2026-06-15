import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { InstallBanner } from './InstallBanner';
import { INSTALL_DISMISSED_KEY } from './useInstallPrompt';
import { I18nProvider } from '@/shared/i18n/I18nProvider';

/**
 * Synthesise the browser's `beforeinstallprompt` event with a spy-able
 * `prompt()`. The hook captures it via a module-level window listener.
 */
const fireBeforeInstallPrompt = () => {
  const prompt = vi.fn(async () => {});
  const event = Object.assign(new Event('beforeinstallprompt'), {
    prompt,
    userChoice: Promise.resolve({ outcome: 'accepted' as const }),
  });
  act(() => {
    window.dispatchEvent(event);
  });
  return prompt;
};

const renderBanner = () =>
  render(
    <I18nProvider initialLocale="en">
      <InstallBanner />
    </I18nProvider>,
  );

beforeEach(() => localStorage.clear());
afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('<InstallBanner /> (MSO-5 A2HS)', () => {
  it('shows nothing until beforeinstallprompt fires', () => {
    const { container } = renderBanner();
    expect(container.firstChild).toBeNull();
  });

  it('appears once the browser offers an install prompt', () => {
    renderBanner();
    fireBeforeInstallPrompt();
    expect(screen.getByText(/add openshiksha to your home screen/i)).toBeInTheDocument();
  });

  it('calls the stashed event prompt() when Install is clicked', async () => {
    renderBanner();
    const prompt = fireBeforeInstallPrompt();
    await userEvent.click(screen.getByRole('button', { name: /^install$/i }));
    expect(prompt).toHaveBeenCalledTimes(1);
  });

  it('persists dismissal and hides the affordance', async () => {
    renderBanner();
    fireBeforeInstallPrompt();
    await userEvent.click(screen.getByRole('button', { name: /dismiss install prompt/i }));
    expect(localStorage.getItem(INSTALL_DISMISSED_KEY)).toBe('1');
    expect(screen.queryByText(/add openshiksha to your home screen/i)).toBeNull();
  });
});
