// Test stub for `virtual:pwa-register/react` (MSO-3). The real module is
// provided by vite-plugin-pwa only during dev/build; under Vitest we alias it
// here so importing PwaUpdater (or App) never fails to resolve. It mimics the
// hook's shape with an inert, never-needs-refresh state.
export const useRegisterSW = () => ({
  needRefresh: [false, () => {}] as [boolean, (v: boolean) => void],
  offlineReady: [false, () => {}] as [boolean, (v: boolean) => void],
  updateServiceWorker: async (_reloadPage?: boolean) => {},
});
