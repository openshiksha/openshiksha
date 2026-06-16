import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { I18nProvider } from '@/shared/i18n/I18nProvider';

// Drive the sync state by feeding fake submission mutations through a mocked
// useMutationState that honours each caller's `select` projection (the component
// projects {status,isPaused}; the badge projects the isPaused boolean).
type FakeMutation = { state: { status: string; isPaused: boolean } };
let fakeMutations: FakeMutation[] = [];

vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...actual,
    useMutationState: ({ select }: { select: (m: FakeMutation) => unknown }) =>
      fakeMutations.map((m) => select(m)),
  };
});

import { SyncStatus, PendingSyncBadge } from './SyncStatus';
import { useSyncState } from './useSyncStatus';

const m = (status: string, isPaused: boolean): FakeMutation => ({ state: { status, isPaused } });

const setOnLine = (value: boolean) =>
  Object.defineProperty(navigator, 'onLine', { configurable: true, value });

const renderEl = (el: React.ReactElement) =>
  render(<I18nProvider initialLocale="en">{el}</I18nProvider>);

beforeEach(() => {
  fakeMutations = [];
  setOnLine(true);
});
afterEach(() => {
  setOnLine(true);
  vi.restoreAllMocks();
});

describe('<SyncStatus />', () => {
  it('renders nothing when idle (nothing queued or in flight)', () => {
    fakeMutations = [m('success', false)];
    const { container } = renderEl(<SyncStatus />);
    expect(container.firstChild).toBeNull();
  });

  it('shows the honest "saved on this device" copy when a write is queued offline', () => {
    fakeMutations = [m('pending', true)];
    renderEl(<SyncStatus />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent(/saved on this device/i);
    expect(status).toHaveTextContent(/will sync/i);
    // Honesty: never claims it reached the server.
    expect(status).not.toHaveTextContent(/saved to server/i);
  });

  it('shows "Syncing…" while a write is actively replaying', () => {
    fakeMutations = [m('pending', false)];
    renderEl(<SyncStatus />);
    expect(screen.getByRole('status')).toHaveTextContent(/syncing/i);
  });

  it('shows the retry copy when a replay failed', () => {
    fakeMutations = [m('error', false)];
    renderEl(<SyncStatus />);
    expect(screen.getByRole('status')).toHaveTextContent(/couldn't sync/i);
  });

  it('prioritises a queued write over an actively-syncing one', () => {
    fakeMutations = [m('pending', true), m('pending', false)];
    renderEl(<SyncStatus />);
    expect(screen.getByRole('status')).toHaveTextContent(/saved on this device/i);
  });
});

describe('useSyncState', () => {
  const Probe = () => <span data-testid="state">{useSyncState()}</span>;

  it('returns idle / queued / syncing / error by priority', () => {
    fakeMutations = [];
    const { rerender } = renderEl(<Probe />);
    expect(screen.getByTestId('state')).toHaveTextContent('idle');

    fakeMutations = [m('error', false)];
    rerender(<I18nProvider initialLocale="en"><Probe /></I18nProvider>);
    expect(screen.getByTestId('state')).toHaveTextContent('error');
  });
});

describe('<PendingSyncBadge />', () => {
  it('renders nothing when no writes are queued', () => {
    fakeMutations = [m('success', false)];
    const { container } = renderEl(<PendingSyncBadge />);
    expect(container.firstChild).toBeNull();
  });

  it('shows a singular count for one queued write', () => {
    fakeMutations = [m('pending', true)];
    renderEl(<PendingSyncBadge />);
    expect(screen.getByRole('status')).toHaveTextContent('1 change waiting to sync');
  });

  it('shows a plural count for several queued writes', () => {
    fakeMutations = [m('pending', true), m('pending', true)];
    renderEl(<PendingSyncBadge />);
    expect(screen.getByRole('status')).toHaveTextContent('2 changes waiting to sync');
  });
});
