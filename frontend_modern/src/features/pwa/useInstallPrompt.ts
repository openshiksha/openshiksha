import { useCallback, useSyncExternalStore } from 'react';

/**
 * MSO-5 — capture the Add-to-Home-Screen flow.
 *
 * `beforeinstallprompt` fires once, early, and often *before* React mounts — so
 * we register the listener at module load and buffer the deferred event here,
 * rather than inside a component effect that would miss it. The hook then reads
 * the buffered state via `useSyncExternalStore`.
 *
 * iOS Safari never fires `beforeinstallprompt`, so `canInstall` simply stays
 * false there and the UI shows nothing (we don't fake an install affordance).
 */

interface BeforeInstallPromptEvent extends Event {
  readonly userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
  prompt: () => Promise<void>;
}

/** localStorage key recording that the user dismissed the install affordance. */
export const INSTALL_DISMISSED_KEY = 'os-install-dismissed';

let deferredPrompt: BeforeInstallPromptEvent | null = null;
let installed = false;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    // Stop Chrome's mini-infobar; we surface our own affordance instead.
    e.preventDefault();
    deferredPrompt = e as BeforeInstallPromptEvent;
    emit();
  });
  window.addEventListener('appinstalled', () => {
    installed = true;
    deferredPrompt = null;
    emit();
  });
}

const isDismissed = (): boolean => {
  try {
    return localStorage.getItem(INSTALL_DISMISSED_KEY) === '1';
  } catch {
    return false;
  }
};

const subscribe = (cb: () => void): (() => void) => {
  listeners.add(cb);
  return () => listeners.delete(cb);
};

// Snapshot must be referentially stable while nothing changed, or
// useSyncExternalStore loops. We derive a boolean and let React compare it.
const getCanInstallSnapshot = (): boolean =>
  deferredPrompt !== null && !installed && !isDismissed();

export interface InstallPrompt {
  /** True when the browser offered an install prompt and the user hasn't dismissed it. */
  canInstall: boolean;
  /** Trigger the native install prompt. No-op if none is buffered. */
  promptInstall: () => Promise<void>;
  /** Persistently dismiss the affordance for this device. */
  dismiss: () => void;
}

export const useInstallPrompt = (): InstallPrompt => {
  const canInstall = useSyncExternalStore(subscribe, getCanInstallSnapshot, () => false);

  const promptInstall = useCallback(async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    // The event is single-use; drop it and notify either way.
    deferredPrompt = null;
    emit();
  }, []);

  const dismiss = useCallback(() => {
    try {
      localStorage.setItem(INSTALL_DISMISSED_KEY, '1');
    } catch {
      // Ignore storage failures (private mode); the prompt just reappears later.
    }
    emit();
  }, []);

  return { canInstall, promptInstall, dismiss };
};
