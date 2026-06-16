# MSO-7 — Offline mutation queue foundation

**Date:** 2026-06-15
**Initiative:** Mobile Shell & PWA-Offline — Batch 2 (offline write-tolerance)
**Classification:** New

## Summary

Wires the *write* half of offline tolerance. The student's submission auto-saves
and final submit become **keyed mutations** with `networkMode: 'offlineFirst'`:
when the network is down they **pause** (durably persisted to IndexedDB) instead
of failing, and replay automatically when connectivity returns — even across a
full reload. No new runtime dependency — this turns on React Query's
offline-mutation + persistence primitives that shipped with Batch 1.

## What changed

- **New `src/shared/query/offlineMutations.ts`:**
  - `registerSubmissionMutationDefaults(queryClient)` — registers
    `setMutationDefaults(['submission','patch'|'create'], { mutationFn,
    networkMode: 'offlineFirst', retry: 3, onSuccess })`. The `mutationFn` and the
    cache-reconciling `onSuccess` live in the defaults (keyed, not a closure) so a
    **rehydrated** paused mutation — which has no component context — can still
    resolve its function and update the cache on replay. `onSuccess` derives the
    assignment from the server response, never a captured variable.
  - `shouldDehydrateSubmissionMutation(mutation)` — persist allowlist: dehydrate a
    mutation only when it is **paused** and `mutationKey[0] === 'submission'`.
    Never auth or any token-bearing mutation.
- **`src/main.tsx`:**
  - Call `registerSubmissionMutationDefaults(queryClient)` **before** the
    `PersistQueryClientProvider` restores the cache (order matters — a rehydrated
    paused mutation looks up its `mutationFn` by key).
  - Flip `shouldDehydrateMutation` from `() => false` to
    `shouldDehydrateSubmissionMutation`.
  - Add the provider's `onSuccess` (fires after the cache restores) →
    `queryClient.resumePausedMutations()`. Mid-session reconnects auto-resume via
    `onlineManager`'s browser online events.
- **`src/features/student/useSubmission.ts`:** `useCreateSubmission` /
  `usePatchSubmission` now reference the keyed defaults by `mutationKey` only (no
  inline `mutationFn`/`onSuccess`). Online behavior is identical; the component
  (`AssignmentDetailPage`) is unchanged — same `mutate` signatures.

## Scope note

Only **patch/submit of an already-created submission** is made offline-durable.
A submission row is created online on first open (Batch 1 already requires an
online first open for offline read), so creating a brand-new submission from a
cold offline start is out of scope for this batch.

## Legacy reference

None — legacy (Django 1.11) was online-only/server-rendered; a dropped connection
lost everything. Offline write-tolerance is new capability the SPA +
service-worker architecture enables. We use React Query's *paused mutation* model
(durable in IndexedDB, replayed even across reload) rather than a naive in-memory
retry, and rely on MSO-6's server idempotency for safe at-least-once replay.

## Tests

`src/shared/query/offlineMutations.test.ts`:
- `shouldDehydrateSubmissionMutation` allowlist: paused submission → true;
  running submission → false; paused non-submission / no key → false.
- Offline round-trip: fire a patch while offline → it **pauses** (not fails) and
  is captured by the allowlist; reconnect + `resumePausedMutations()` drives the
  keyed `mutationFn` and the default `onSuccess` reconciles the cache.
- Rehydration-safety: a mutation created with only a `mutationKey` still resolves
  its function from the registered defaults.

Regression: student feature suite (38 tests) green; `npx tsc --noEmit`, eslint,
`npm run build`, and the bundle budget (144.33 kB ≤ 160 kB, no new dep) all green.

## Next steps

- MSO-8 — "Saved offline · will sync" status UX (reads this queue's state).
- MSO-9 — offline final-submit (optimistic submitted state, replays onto MSO-6).
