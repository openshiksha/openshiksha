# M2-02 — Mobile nav polish

**Classification:** Improve.

## Summary
Now that the bottom tab bar (M5-01 / #195) carries the primary navigation on
mobile, the hamburger sheet is repurposed as a focused **account drawer**
instead of a redundant copy of the tabs. Also catches the navbar up to the V2
token system (the mobile dropdown still wore `text-gray-*` / `bg-gray-*` /
`text-red-*` classes) and adds the accessibility plumbing the file was
missing.

## Files changed
- `frontend_modern/src/features/layout/Navbar.tsx`

## What changed
- **Mobile sheet contents** — removed the duplicated Dashboard / Browse /
  Learning Path / Questions links (all already in the bottom tab bar) and
  reorganised the sheet around an explicit "Account" section: identity row
  (avatar + name + role chip), Profile, **My Progress** for students (which
  is *not* in the bottom tabs), and Sign out. Less clutter, no overlap.
- **Desktop user-menu** — gained the same "My Progress" shortcut for
  students; also got proper `role="menu"`/`role="menuitem"` semantics.
- **Tokens** — all `text-gray-*` / `bg-gray-*` / `border-gray-*` / `text-red-*`
  / `bg-red-*` classes swapped for `ink-*` / `rose-*` so the navbar matches
  the rest of the V2 surfaces and survives the `primary`-blue retirement.
- **Accessibility**
  - `<nav aria-label="Top">` and `navbar-mobile-sheet` id wired to the
    hamburger's `aria-controls`.
  - Dynamic hamburger `aria-label` ("Open account menu" / "Close account
    menu") and `aria-haspopup="menu"` on the desktop avatar button.
  - Active desktop link sets `aria-current="page"`.
  - Focus-visible brand ring on every interactive (logo link, desktop
    avatar, hamburger, all menu items).
  - **ESC closes** both the desktop dropdown and the mobile sheet; closing
    the sheet returns focus to the hamburger toggle.
  - Logo link rendered as an inline-flex with a rounded focus target.
- **Safe-area** — `pt-[env(safe-area-inset-top)]` so the sticky nav clears
  the notch on iOS, matching `BottomNav`'s safe-area-bottom pattern.

## What was preserved
- Desktop primary nav links (Dashboard / Browse / Learning Path / Questions /
  Admin / Parent Dashboard) unchanged in behaviour and visible breakpoint.
- All existing routes, role guards, `useAuth` wiring, and the
  close-on-route-change pattern.
- The 17/89 vitest suite still passes — no test depended on the now-removed
  mobile primary nav links.

## Continuous improvement
- ESC handling is added once at the `Navbar` level for both dropdowns; no
  per-component wiring needed.
- Removes the last `text-gray-*` / `text-red-*` consumer in
  `src/features/layout/`.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green
  (17 files / 89 tests).
- Grep `text-gray-|bg-gray-|border-gray-|text-red-|bg-red-` in
  `Navbar.tsx` → 0.

## Next
M3-03 Public Enquire page.
