# Screen-reader sign-off — manual test script (A11Y-17)

Part of the [Accessibility — WCAG 2.1 AA](../2026-accessibility-wcag-aa.md)
initiative (**DoD item 5** — keyboard-only + screen-reader sign-off).

This is the **manual evidence template**. The automated specs
(`e2e/a11y.spec.ts` axe gate, `e2e/keyboard.spec.ts` keyboard gate) cover
structure, contrast, and keyboard operability; a real screen-reader pass is the
remaining human check. Run this script per release-significant a11y change, record
the result in the per-journey tables below, and link the filled copy from the PR.

## How to run

| Platform | Screen reader | Browser | Launch |
|---|---|---|---|
| Windows | **NVDA** (free, [nvaccess.org](https://www.nvaccess.org/)) | Firefox or Chrome | `Ctrl+Alt+N` |
| macOS / iOS | **VoiceOver** (built-in) | Safari | `Cmd+F5` (mac) / triple-click side button (iOS) |

Core commands: NVDA — `Tab`/`Shift+Tab` (focus), `↓`/`↑` (read next/prev),
`NVDA+Space` (forms mode), `Insert+F7` (elements list). VoiceOver — `VO+→`/`VO+←`
(navigate), `VO+Space` (activate), `VO+U` (rotor).

**Pass criteria per step:** the expected announcement is spoken, focus order is
logical, no control is silent or unlabeled, and dynamic changes (status messages)
are announced without stealing focus.

---

## Journey 1 — Sign in

| # | Action | Expected announcement | NVDA | VO | Notes |
|---|---|---|---|---|---|
| 1 | Load `/login` | "OpenShiksha", heading level 1; then "Email, edit" | ☐ | ☐ | |
| 2 | Tab to password | "Password, edit, protected" | ☐ | ☐ | |
| 3 | Submit empty | Inline error announced (field `aria-describedby`) | ☐ | ☐ | |
| 4 | Submit valid | Route change announced; lands on dashboard `h1` | ☐ | ☐ | |

## Journey 2 — Register (open student)

| # | Action | Expected announcement | NVDA | VO | Notes |
|---|---|---|---|---|---|
| 1 | Load `/register/open` | Form heading `h1`; first field labelled | ☐ | ☐ | |
| 2 | Tab through fields | Each control names itself (no placeholder-only) | ☐ | ☐ | |
| 3 | Validation error | Error text announced, focus stays usable | ☐ | ☐ | |

## Journey 3 — Browse & start practice

| # | Action | Expected announcement | NVDA | VO | Notes |
|---|---|---|---|---|---|
| 1 | Load `/student` | "Skip to main content" link reachable first | ☐ | ☐ | |
| 2 | Activate skip link | Focus moves into `#main-content` | ☐ | ☐ | gated in `keyboard.spec.ts` |
| 3 | Open an assignment | Assignment title `h1` announced | ☐ | ☐ | |

## Journey 4 — Practice + submit (highest priority)

| # | Action | Expected announcement | NVDA | VO | Notes |
|---|---|---|---|---|---|
| 1 | Read a question | Question text + options announced as a group | ☐ | ☐ | |
| 2 | Select an MCQ option | Selected state announced | ☐ | ☐ | |
| 3 | Submit | **Score card announced via `role=status`/`aria-live=polite`** | ☐ | ☐ | A11Y-17 fix; asserted in `AssignmentDetailPage.offline.test.tsx` |
| 4 | Submit while offline | "Saved on this device · will sync" announced (`SyncStatus`, `role=status`) | ☐ | ☐ | MSO-8 |

## Journey 5 — Parent dashboard

| # | Action | Expected announcement | NVDA | VO | Notes |
|---|---|---|---|---|---|
| 1 | Load `/parent` | Dashboard `h1`; child cards as a list | ☐ | ☐ | |
| 2 | Open insights | Insights `h1`; empty/summary state announced | ☐ | ☐ | |

---

## Announce-region inventory (the automatable slice)

Dynamic regions audited for correct live-region semantics. `role=status` /
`aria-live="polite"` for non-urgent status; `aria-live="assertive"` /
`role=alert` only for errors. **Scope the live region to the single status node —
never wrap a whole form**, or every keystroke floods the user.

| Region | Component | Semantics | Status |
|---|---|---|---|
| Post-submit score / grading / offline-submit card | `student/AssignmentDetailPage.tsx` | `role=status` `aria-live=polite` | ✅ added A11Y-17 (asserted) |
| "Saved on this device · will sync" | `student/SyncStatus.tsx` | `role=status` `aria-live=polite` | ✅ MSO-8 |
| Offline / reconnect banner | `layout/OfflineBanner.tsx` | live region | ✅ (covered by test) |
| App-update available banner | `pwa/UpdateBanner.tsx` | live region | ✅ (covered by test) |
| Announcements banner | `student/AnnouncementsBanner.tsx` | live region | ✅ |
| Loading spinners / skeletons | `shared/ui/LoadingSpinner.tsx`, `Skeleton.tsx` | `role=status` | ✅ |

### Remaining (Batch 4 follow-up)

- **Dialog focus management** — the QuestionBank "Add to set" side-sheet
  (`teacher/QuestionBankPage.tsx → AddToProblemSetSheet`) moves focus inside on
  open and closes on Escape, but still needs a true focus **trap** (Tab bounded
  within the dialog) and focus **restore** (return to the trigger on close) —
  WCAG 2.4.3 / 2.1.2. Once implemented, gate it in `keyboard.spec.ts`.
- App has **no global toast component**; status is surfaced inline per the regions
  above. If a toast is later introduced it must be a polite live region.
