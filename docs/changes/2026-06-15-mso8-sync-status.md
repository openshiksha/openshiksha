# MSO-8 — "Saved offline · will sync" status UX

**Date:** 2026-06-15
**Initiative:** Mobile Shell & PWA-Offline — Batch 2 (offline write-tolerance)
**Classification:** New

## Summary

Makes the MSO-7 offline submission queue **visible and honest** to the student.
A slim, localized, `aria-live` indicator on the assignment page tells them whether
their work is queued on the device, actively syncing, or failed to sync — and a
small global badge in the app shell surfaces the pending count even off the
assignment page. Honesty over magic (initiative principle 4): the copy says
"Saved on this device", never "Saved to server", while a write is merely queued.

## What changed

- **New `src/features/student/useSyncStatus.ts`:**
  - `useSyncState()` → `'idle' | 'queued' | 'syncing' | 'error'`, derived from
    `useMutationState({ filters: { mutationKey: ['submission'] } })`. Priority:
    queued (paused/offline) > syncing (active replay) > error (settled failure) >
    idle.
  - `usePendingSyncCount()` → number of paused (queued) submission writes.
- **New `src/features/student/SyncStatus.tsx`:**
  - `SyncStatus` — inline assignment-page indicator; renders nothing when idle, a
    slim localized line otherwise (`role="status"`, `aria-live="polite"`).
  - `PendingSyncBadge` — unobtrusive global badge; hidden when nothing is queued,
    singular/plural localized count otherwise.
- **`AssignmentDetailPage.tsx`** — renders `<SyncStatus />` under the header.
- **`AppShell.tsx`** — renders `<PendingSyncBadge />` beside the offline banner.
- **i18n** — new `sync.` cluster (`savedOffline`, `syncing`, `synced`,
  `syncFailed`, `pendingOne`, `pendingMany`) in `en.ts` + `hi.ts` at full parity.
  (Marathi was removed from the product on 2026-06-14, so only en/hi apply.)

## Legacy reference

None — offline write status is a new capability. Reuses the Batch 1
`useOnlineStatus` hook + slim-banner pattern and the LA i18n framework.

## Tests

`src/features/student/SyncStatus.test.tsx` (mocks `useMutationState`, honouring
each caller's `select` projection): idle → renders nothing; queued → "Saved on
this device · will sync" (and asserts it never says "saved to server"); syncing →
"Syncing…"; error → retry copy; queued takes priority over syncing; badge hidden
at 0, singular at 1, plural at 2; `useSyncState` priority. i18n parity guard green
for the `sync.` keys. Full suite (429) + tsc + lint + build + bundle budget
(145.87 kB ≤ 160 kB) green.

## Next steps

MSO-9 — offline final-submit: optimistic submitted state + pending-grade card,
surfacing the `syncFailed` state from this PR when a replay ultimately fails.
