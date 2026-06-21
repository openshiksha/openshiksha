import { useRegisterSW } from 'virtual:pwa-register/react';
import { UpdateBanner } from './UpdateBanner';

/**
 * Registers the service worker (MSO-3) and surfaces an "update available"
 * prompt when a new build has been precached and is waiting.
 *
 * `useRegisterSW` auto-registers on mount. In dev the plugin's
 * `devOptions.enabled: false` means the virtual module is a no-op, and in the
 * test env the module is stubbed (see src/test-setup.ts), so this component is
 * inert outside a production build. `registerType: 'autoUpdate'` activates the
 * new SW immediately on refresh, so the prompt only needs to trigger a reload.
 */
export const PwaUpdater = () => {
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  if (!needRefresh) return null;

  return <UpdateBanner onRefresh={() => updateServiceWorker(true)} />;
};
