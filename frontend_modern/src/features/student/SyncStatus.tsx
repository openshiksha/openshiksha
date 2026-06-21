import { useOnlineStatus } from '@/shared/hooks/useOnlineStatus';
import { useT } from '@/shared/i18n';
import { useSyncState, usePendingSyncCount } from './useSyncStatus';

/**
 * MSO-8 — honest "Saved offline · will sync" status for the student.
 *
 * Reads the MSO-7 submission mutation queue and tells the student whether their
 * work is queued on the device, actively syncing, synced, or failed to sync.
 * Principle 4 of the initiative (honesty over magic): we never claim "Saved to
 * server" while a write is merely queued — the copy says "Saved on this device".
 */

/**
 * Inline indicator for the assignment page. Renders nothing when idle (online,
 * nothing queued) — a quiet default — and a slim, localized line otherwise.
 */
export const SyncStatus = () => {
  const state = useSyncState();
  const t = useT();

  if (state === 'idle') return null;

  const { label, tone, icon } = {
    queued: {
      label: t('sync.savedOffline'),
      tone: 'text-amber-800',
      icon: '⤓',
    },
    syncing: {
      label: t('sync.syncing'),
      tone: 'text-ink-500',
      icon: '↻',
    },
    error: {
      label: t('sync.syncFailed'),
      tone: 'text-rose-700',
      icon: '⚠',
    },
  }[state];

  return (
    <p
      role="status"
      aria-live="polite"
      className={`flex items-center gap-1.5 text-xs font-medium ${tone}`}
    >
      <span aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </p>
  );
};

/**
 * Global pending-sync badge for the app shell, visible even off the assignment
 * page. Unobtrusive: hidden when nothing is queued.
 */
export const PendingSyncBadge = () => {
  const online = useOnlineStatus();
  const count = usePendingSyncCount();
  const t = useT();

  if (count === 0) return null;

  const label =
    count === 1 ? t('sync.pendingOne', { count }) : t('sync.pendingMany', { count });

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-2 bg-amber-50 px-4 py-1.5 text-center text-xs font-medium text-amber-800"
    >
      <span aria-hidden="true">{online ? '↻' : '⤓'}</span>
      <span>{label}</span>
    </div>
  );
};
