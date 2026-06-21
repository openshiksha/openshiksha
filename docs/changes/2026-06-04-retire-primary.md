# M6-02 — Retire the legacy `primary` blue token

**Classification:** Improve (cleanup).

## Summary
With the M4 batch closing every authenticated surface on V2 brand, the legacy
`primary` blue palette and its associated `.btn-primary`/`.btn-secondary`/
`.card`/`.input` helper classes are no longer consumed anywhere in `src/`.
This PR deletes them.

## Files changed
- `frontend_modern/tailwind.config.js` — drop the `primary` palette; refresh
  the comment on the `brand` palette to note the retirement.
- `frontend_modern/src/index.css` — drop the four legacy helper classes;
  refresh the top-of-file comment.

## Verification
- `grep -rnE "\bprimary-[0-9]|\bbtn-primary\b|\bbtn-secondary\b" src/` → 0.
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.

## Why now
M4 closed today (PRs #188–#192). With no remaining consumer, keeping the token
+ classes around just invites new code to reach for them. Removing them is a
hard guarantee that V2 is the only language.

## Next
- M7-03 Browse filter wiring.
- M5-01 Mobile bottom tab bar (student).
