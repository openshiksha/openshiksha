# PWA / Offline-write — manual test checklist

**Initiative:** Mobile Shell & PWA-Offline (Batch 2, 2026-06-15) — offline
*write*-tolerance

Batch 2 makes the student core loop survive a dropped connection for **writes**:
auto-saves and final submit are queued durably (MSO-7), shown honestly (MSO-8),
submittable offline (MSO-9), and replay **exactly once** onto an idempotent server
(MSO-6). The queue + IndexedDB persistence + real service worker can't be fully
exercised by Vitest, so run this checklist against a production build.

This is the sibling of Batch 1's read-tolerance checklist
(`docs/perf/2026-06-14-pwa-offline-manual-test.md`); run that first to confirm
the shell + reads still boot offline.

## Setup

```bash
cd frontend_modern
npm run build
npm run preview   # serves dist/ on http://localhost:4173 (localhost = SW-eligible)
```

Open the preview URL in Chrome or Edge and sign in as a **student** with at least
one open (not-yet-submitted) assignment. Keep DevTools → Network open to toggle
**Offline**.

## 1. Queue an auto-save offline (MSO-7 + MSO-8)

- [ ] Open an assignment **online** so its questions and the submission row load.
- [ ] DevTools → Network → **Offline**.
- [ ] Type/select answers. Within ~2 s the assignment header shows the honest
      sync line: **"Saved on this device · will sync when you're back online"**
      (`role="status"`). It does **not** say "saved to server".
- [ ] A small **pending-sync badge** appears near the offline banner in the app
      shell ("N change(s) waiting to sync"), visible even if you navigate away.

## 2. Survive a reload while offline (MSO-7 persistence)

- [ ] Still offline, **reload** the page. The shell boots (Batch 1), the
      assignment re-opens with your typed answers, and the queued write is still
      pending (the badge persists) — the paused mutation was rehydrated from
      IndexedDB.

## 3. Submit while offline (MSO-9)

- [ ] Still offline, tap **Submit assignment** → confirm. The page flips
      immediately to a **neutral** submitted card reading **"Submitted — will be
      graded when you're back online"** (no score band, no fake %). The answer
      inputs lock.

## 4. Reconnect → replay exactly once (MSO-6 + MSO-7)

- [ ] DevTools → Network → **Online** (or **Back online**). The queued writes
      replay automatically (the badge drains to zero; the sync line shows
      "Syncing…" then clears).
- [ ] The submitted card reconciles to the **real score band** (red/amber/green)
      once grading completes — refresh if grading is still async.
- [ ] Confirm in the backend/admin that the submission was graded **once** (a
      single set of ticks, one score) — the replayed submit did **not** re-grade
      (MSO-6).

## 5. Double-submit race (MSO-6 idempotency)

- [ ] Repeat 1–3, then go online and quickly **re-submit** the same assignment
      from another tab/device before the queue drains. The second submit is a
      **no-op returning the same score** — no error, no second grade.

## 6. Localized copy (en / हिं)

- [ ] Switch language to **हिंदी** and repeat 1 + 3. The sync line
      ("इस डिवाइस पर सहेजा गया · ऑनलाइन होने पर सिंक होगा") and the offline-submit
      card ("ऑनलाइन होने पर जाँच की जाएगी") are localized.

> Note: Marathi (मराठी) was removed as a product language on 2026-06-14, so only
> en/हिं are exercised here.

## Pass criteria

Offline answers and submits are **never lost**, the UI is **honest** about what is
queued vs. saved-to-server, and every queued write grades **exactly once** on
reconnect with no double-grading.
