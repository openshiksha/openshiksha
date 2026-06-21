# MSO-10 — Mobile Shell & PWA-Offline Batch 2 close-out

**Date:** 2026-06-15
**Initiative:** Mobile Shell & PWA-Offline — Batch 2 (offline write-tolerance)
**Classification:** Docs

## Summary

Closes out Batch 2 (offline *write*-tolerance, MSO-6..9): adds the manual
offline-write test checklist, appends the ledger rows, marks the "Offline
write-tolerance" later-phase item shipped, and flips the STATUS headline.

## What changed

- **New `docs/perf/2026-06-15-pwa-offline-write-manual-test.md`** — manual
  end-to-end checklist (sibling to Batch 1's read-tolerance checklist): open
  online → go offline → answers queue ("saved on this device") → reload survives →
  submit offline ("will be graded when back online") → reconnect → queued writes
  replay, score reconciles, **no double-grade**; double-submit race is a no-op;
  repeat in en/हिं.
- **`docs/initiatives/2026-mobile-shell-pwa-offline.md`** — appended ledger rows
  for MSO-6 (#367), MSO-7 (#368), MSO-8 (#369), MSO-9 (#370); added the
  "Batch 2 shipped 2026-06-15" summary; marked the Batch 2 section ✅ and the
  "Offline write-tolerance" later-phase item shipped.
- **`docs/initiatives/STATUS.md`** — headline flipped from "Batch 2 planned" to
  "Batch 2 SHIPPED", with per-PR links and the remaining next phases (route-level
  mobile layouts; web push for due-date reminders).

## Batch 2 recap

| PR | Increment | Classification |
|---|---|---|
| #367 | MSO-6 — replay-safe / idempotent submission writes | Improve |
| #368 | MSO-7 — offline mutation queue foundation | New |
| #369 | MSO-8 — "Saved offline · will sync" status UX | New |
| #370 | MSO-9 — offline final-submit | New |
| (this) | MSO-10 — batch close-out | Docs |

The student core loop is now write-tolerant offline: auto-saves and final submit
queue durably to IndexedDB, replay on reconnect, and grade exactly once on a
server hardened idempotent in MSO-6 — no new runtime dependency, riding Batch 1's
persister + `useOnlineStatus` + the LA i18n framework.

## Next steps

- Route-level mobile layouts for dense teacher tables.
- Web push for due-date reminders (the email reminder already exists).
