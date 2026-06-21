import React, { lazy, Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient } from '@tanstack/react-query';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import App from './App';
import './index.css';
import {
  createIDBPersister,
  shouldDehydrateQuery,
  CACHE_BUSTER,
  PERSIST_MAX_AGE,
} from './shared/query/persist';
import {
  registerSubmissionMutationDefaults,
  shouldDehydrateSubmissionMutation,
} from './shared/query/offlineMutations';

// Create a client. `gcTime` is bumped to 24h so entries survive long enough to
// be persisted to / restored from IndexedDB (MSO-4); `staleTime` stays at 5 min
// so online sessions still refetch fresh data.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: PERSIST_MAX_AGE, // 24h — keep entries alive long enough to persist
    },
  },
});

// MSO-7: register the keyed submission mutation defaults BEFORE the persister
// restores the cache, so a rehydrated paused mutation can resolve its
// `mutationFn` by `mutationKey` and replay after a reload.
registerSubmissionMutationDefaults(queryClient);

// IndexedDB-backed persister so the last-fetched student core-loop reads
// (assignments, dashboard, due-for-review) are readable offline, and queued
// offline submission writes (MSO-7) survive a reload. Reads use the MSO-4
// allowlist; mutations dehydrate only when paused + in the `submission` family.
const persister = createIDBPersister();

// ReactQueryDevtools is dev-only. Production builds must never ship it — the
// import is wrapped in a `lazy()` that the bundler dead-code-eliminates behind
// the `import.meta.env.DEV` guard.
const ReactQueryDevtools = import.meta.env.DEV
  ? lazy(() =>
      import('@tanstack/react-query-devtools').then((m) => ({ default: m.ReactQueryDevtools })),
    )
  : null;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{
        persister,
        maxAge: PERSIST_MAX_AGE,
        buster: CACHE_BUSTER,
        dehydrateOptions: {
          shouldDehydrateQuery,
          // MSO-7: persist only PAUSED submission mutations (queued offline). The
          // server is idempotent (MSO-6), so replaying these at-least-once is safe.
          shouldDehydrateMutation: shouldDehydrateSubmissionMutation,
        },
      }}
      onSuccess={() => {
        // The cache (and any persisted paused mutations) has been restored — flush
        // queued offline writes. Mid-session reconnects auto-resume via
        // onlineManager's browser online events.
        void queryClient.resumePausedMutations();
      }}
    >
      <App />
      {ReactQueryDevtools ? (
        <Suspense fallback={null}>
          <ReactQueryDevtools initialIsOpen={false} />
        </Suspense>
      ) : null}
    </PersistQueryClientProvider>
  </React.StrictMode>,
);
