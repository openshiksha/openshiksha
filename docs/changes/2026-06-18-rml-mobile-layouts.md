# 2026-06-18 — RML-1..5: Route-level mobile layouts (Mobile Shell Batch 4)

**Initiative:** [Mobile Shell & PWA-Offline](../initiatives/2026-mobile-shell-pwa-offline.md) — Batch 4, the final later-phase. **This batch completes the initiative.**

**Classification:** New (RML-1 primitive) + Improve (RML-2..4) + Docs (RML-5).

## Summary

The student core loop has been mobile-first since the V2 overhaul, but several
**teacher** surfaces were ported table-first for desktop and only band-aided with
`overflow-x-auto` — which on a phone means pinch-zoom-and-scroll. This batch makes
the dense teacher surfaces readable and usable on a 360 px screen, via a small
shared `ResponsiveTable` primitive and per-surface mobile-first stacking.

| PR | Item | Surface |
|---|---|---|
| [#382](https://github.com/openshiksha/openshiksha/pull/382) | RML-1 | `shared/ui/ResponsiveTable` + ClassHealthPanel |
| [#383](https://github.com/openshiksha/openshiksha/pull/383) | RML-2 | Assignment-detail submissions (+ localize) |
| [#384](https://github.com/openshiksha/openshiksha/pull/384) | RML-3 | Create-Question form density |
| [#385](https://github.com/openshiksha/openshiksha/pull/385) | RML-4 | Open-Response grading layout |
| (this) | RML-5 | docs + ledger + STATUS close-out |

## The `ResponsiveTable` contract

`frontend_modern/src/shared/ui/ResponsiveTable.tsx` — generic, typed, dependency-free:

```tsx
interface ResponsiveColumn<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;   // renders both the desktop cell and the card value
  align?: 'left' | 'right';
  primary?: boolean;             // becomes the mobile card heading (no label)
}
<ResponsiveTable columns rows rowKey caption? aria-label? />
```

- **≥ `sm` (640 px):** a real semantic `<table>` (`hidden sm:table`) styled with the
  V2 `ink-*` tokens — `thead`, row borders, right-alignable columns.
- **< `sm`:** a `<ul className="sm:hidden">` where each row is a card — the `primary`
  column as the heading, every other column as a `<dl>` label/value pair.

It follows the repo's established `hidden sm:table` / `sm:hidden` **dual-render**
convention (`Navbar`, `BottomNav`, `DueForReviewPanel`) rather than a runtime
`matchMedia`/`useIsMobile` hook — so there is no hydration/SSR-style flicker and no
JS cost. Exported from `shared/ui/index.ts` and demoed on the `/design` route.

## What changed per surface

- **RML-1 / ClassHealthPanel** — replaced the `-mx-1 overflow-x-auto` + `min-w-[22rem]`
  table with `<ResponsiveTable>` (Chapter [primary] / Avg / Struggling / Status). The
  status dot + label and the `n/m struggling` cell moved into `cell` renderers; the
  existing `teacher.th*` i18n keys are reused — no new strings.
- **RML-2 / TeacherAssignmentDetailPage** — converted the submissions `<table>` to
  `<ResponsiveTable>` (student name = `primary`; `ScoreBadge` + status pills
  preserved). **Localization decision:** this page had slipped the LA-6
  teacher-chrome pass and carried hardcoded English, a regression against the
  Language Access parity contract — so while in the file we routed every string
  through `useI18n()`, added `teacher.ad*` keys in **en + hi** (the only two locales
  after the Marathi pilot was removed), and moved the two date renders to the
  locale-aware `useFormat()` helper. The i18n surface was small enough to keep in the
  same PR (the plan allowed splitting to RML-2b if it ballooned — it didn't).
- **RML-3 / CreateQuestionPage** — mobile-first grids: AI panel `grid-cols-3` →
  `grid-cols-1 sm:grid-cols-3`, chapter `grid-cols-2` → `grid-cols-1 sm:grid-cols-2`;
  subpart tab buttons given a `min-h-[44px]` touch target. The variable-constraint
  rows already `flex-wrap` and the KaTeX preview already stacks below the editor, so
  no change was needed there. No form logic touched.
- **RML-4 / OpenResponseGradingPage** — review-form field row `flex-wrap` →
  `flex-col sm:flex-row`; marks input `w-full sm:w-24`; comment `sm:min-w-[12rem]`;
  response blockquote `break-words`. The AI-suggest / teacher-finalise flow is
  untouched.

## Tests

- New `ResponsiveTable.test.tsx`: table + card list both present with the correct
  breakpoint classes; header/row counts; primary-as-heading vs label/value pairs;
  `rowKey`; empty state.
- New `TeacherAssignmentDetailPage.test.tsx`: submissions render as table + cards;
  graded vs pending badges; empty state; Hindi heading (dynamic-import dict awaited).
- `CreateQuestionPage.test.tsx` / `OpenResponseGradingPage.test.tsx`: existing suites
  pass + a class-presence assertion for the mobile-first grid/flex base classes.
- i18n key-parity guard green (en + hi both carry every new `teacher.ad*` key).
- Each PR: `npm run test` / `tsc --noEmit` / `eslint` / `npm run build` — entry chunk
  unchanged vs the 160 kB CI guard.

## Migration notes

None — frontend-only; no backend, no dependency, no schema.

## Next steps

Mobile Shell & PWA-Offline is **complete** (first-phase DoD + both later phases).
The STATUS board has **no unblocked next bet** — the next planning run promotes a
fresh top initiative. Candidates: **AI-tutor rebase** (`ai/2026-06-04-ai-tutor-chat`,
a ~5k-line diverged branch), an **`/ai/predictions/` teacher surface**, or a formal
**accessibility audit** (WCAG 2.1 AA). Language Access **LA-10** (authored-content
translation) remains blocked on product design.
