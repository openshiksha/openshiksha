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

// IndexedDB-backed persister so the last-fetched student core-loop reads
// (assignments, dashboard, due-for-review) are readable offline. Reads only;
// the dehydrate allowlist excludes auth + mutations (see shared/query/persist).
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
          // Never persist mutations — restoring one could double-submit.
          shouldDehydrateMutation: () => false,
        },
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
