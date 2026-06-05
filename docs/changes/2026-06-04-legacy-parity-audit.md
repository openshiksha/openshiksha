# M7-04 — Legacy feature-parity audit

**Classification:** Docs.

## Summary
The first proper M7-04 deliverable: a single audit doc that maps **every
legacy Django 1.11 app** to its modern Django 4.2 + React equivalent, calls
out gaps as ⏳ TODO or 🟡 partial, and gives a deletion checklist for any
legacy app the team decides to retire.

## Files changed
- **New** `docs/initiatives/legacy-feature-parity.md` — source-of-truth audit.

## Why now
Most of the legacy mapping lived in `CLAUDE.md`'s routine prompt as a "Already
ported / What's left" table. That prompt is invisible to a reader browsing
`docs/`, and the table is bullets without a status column, so it's hard to
*scan* the modern app's parity surface. Pulling the audit into
`docs/initiatives/` gives it a stable URL, lets contributors tick rows as ports
land, and surfaces the gaps the routine table hand-waved over.

## What it captures
- An at-a-glance row per legacy app (`core`, `edge`, `grader`, `focus`,
  `croupier`, `sphinx`, `cabinet`, `pylon`, `concierge`, `lodge`, `ink`,
  `challenge`, `frontend`) with a ✅ / 🟡 / ⛔ / ⏳ status, modern home, and
  one-line notes.
- Four "by audience" tables — Student, Teacher, Parent, Admin — that walk the
  capabilities a user can actually exercise, with PR links to every V2 port.
- A public/marketing table for `/`, `/login`, `/register/*`, `/enquire`.
- Seven concrete TODOs split into "small follow-up" vs. "out of scope until
  product asks" — the first one (concierge enquiry email no-op because
  `ADMINS` is unset) is exactly the question that came up while shipping
  M3-03.
- A retirement checklist so anyone proposing `git rm -r <legacy_app>/` knows
  the gate.

## Verification
- Docs-only change; no code touched.
- Cross-checked against `CLAUDE.md` mapping and recent PR history.

## Next
This is the last M5/M6/M7 backlog row from today's "make PRs for all of these
top to bottom" pass. The V2 initiative status board (`STATUS.md`) and the
ledger in `2026-design-system-v2.md` are now both up to date; the parity audit
is the durable answer for "what does the modern app still owe the legacy app?"
