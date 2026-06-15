# MSO-4 — Persist React Query cache to IndexedDB

**Date:** 2026-06-14
**Classification:** New
**Initiative:** Mobile Shell & PWA-Offline (Batch 1, PR 4)

## Summary

Persist the React Query cache to IndexedDB so a student who loaded their work
online can re-open it offline and read every question. Paired with the MSO-3
precached shell (which lets the app boot offline), this delivers the initiative's
core read-tolerance: dashboard + assignment list + assignment detail +
due-for-review all readable with no network.

## Legacy reference

None — Django 1.11 was server-rendered/online-only. New SPA capability.

## What changed

- **`frontend_modern/src/shared/query/persist.ts`** (new) — the persistence
  policy, with the offline-read allowlist as a unit-testable predicate:
  - `shouldPersistQueryKey(queryKey)` — allowlists only the student core-loop
    roots (`assignments`, `assignment`, `student` streak, `srs`) plus the
    student-facing `ai` sub-keys (`recommendations`, `practice-plan`,
    `learning-paths`, `explanations`). **Never** persists `auth`, and excludes
    teacher/admin/parent data and the question bank (no PII / bloat).
  - `shouldDehydrateQuery(query)` — persists only **successful** allowlisted
    queries.
  - `createIDBPersister()` — `idb-keyval`-backed persister (~1 kB, lazy).
  - `CACHE_BUSTER` (bump on query-shape change) + `PERSIST_MAX_AGE` (24h).
- **`frontend_modern/src/main.tsx`** — replaced `QueryClientProvider` with
  `PersistQueryClientProvider`; bumped `gcTime` to 24h (entries survive long
  enough to persist/restore) while keeping `staleTime` at 5 min; wired the
  persister, `buster`, `maxAge`, `shouldDehydrateQuery`, and
  `shouldDehydrateMutation: () => false` (reads only — never replay a mutation).
- **deps** — `@tanstack/react-query-persist-client` + `idb-keyval`.

## Technical details

- Reads-only by construction: mutations are never dehydrated, so a restored
  cache can never double-submit. Auth/JWTs live in the auth store, not the query
  cache, and are excluded defensively anyway.
- `buster` keyed to `CACHE_BUSTER` discards an incompatible persisted cache after
  a deploy that changes query shape.

## Tests

- `persist.test.ts` (6) — allowlist accepts core-loop reads + student AI sub-keys;
  rejects auth/teacher/admin/parent/questions and non-string roots;
  `shouldDehydrateQuery` requires success; `createIDBPersister` round-trips +
  removes via a mocked `idb-keyval`.
- Full gate: `tsc --noEmit` clean, `lint` clean, `vitest run` 408 passing,
  `npm run build` ok, bundle budget green (138 kB vs 160 kB — `idb-keyval` is
  ~1 kB and lazy).

## Migration notes

None — frontend-only, additive. Two new runtime deps.

## Next steps

- MSO-5: install prompt + the manual offline-test checklist (load assignment →
  offline → reload → read questions) that exercises MSO-3 + MSO-4 together.
