# M4-07c — Create-Question authoring page → V2

**Classification:** Improve.

## Summary
Migrates `CreateQuestionPage` — the densest file in today's batch (~90 legacy
colour refs) — from `primary`/`indigo`/cold-`gray` to V2 brand/ink tokens.
Class-name changes only; the M7-01 `RichContent` live-preview wiring, the AI
generation state machine (#185, Gemini JSON mode), and the variable-constraints
panel logic are all preserved byte-for-byte.

## Files changed
- `frontend_modern/src/features/teacher/CreateQuestionPage.tsx`

## What changed (mechanical sweep)
- `bg-indigo-*` / `text-indigo-*` / `border-indigo-*` → `brand-*` (so the AI
  panel, the active subpart tab, the difficulty selector, and the primary
  Save/Generate buttons all wear brand orange).
- `bg-gray-*` / `text-gray-*` / `border-gray-*` → `ink-*` (warm paper tones).
- Status colours `text-red-*` / `text-green-*` → `text-rose-*` / `text-emerald-*`
  in the draft card and validation strip.
- Page heading uplifted to `font-display font-semibold` to match the rest of
  the V2 surfaces.
- `focus:ring-indigo-500` → `focus:ring-brand-500` on every form control.

## What was preserved
- The `RichContent` block preview (`renderPreview`) wiring — only the
  container around it was restyled (`bg-gray-50` → `bg-ink-50`).
- `useGenerateQuestions` + `AIGenerationPanel` state machine, drafts, retry
  flow, skeleton loaders, "Use this" handler.
- All `useState`/`useCallback` logic, all form controls' `onChange`/`onClick`,
  the variable-constraints sync (`syncVariableConstraints`), the live
  variable preview, the `handleSubmit` payload shape.
- The `DraftCard` markup and behaviour; only the inline pill/button/border
  colours moved to tokens.

## Continuous improvement
- Active subpart tab now reads as the brand "unlock" colour (brand-600), so
  the authoring surface no longer looks like a stock indigo CRUD form.
- Status colours (red/green) replaced with the system's semantic
  `rose`/`emerald` so the page matches the AlertsPanel / TeacherAssignmentDetail
  treatments shipped today.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.
- Grep `primary|indigo|blue-|gray-50|text-gray-` in the file → 0.
- Grep `gray-[0-9]+` → 0 (no orphan stock-gray classes left).

## Risk note
- The reskin fits in one PR (class-name swaps only); the
  variable-constraints-panel split-out fallback in the plan was not needed.
- Behavior is purely visual — no API or state-machine change. The AI
  generation flow, MCQ option editing, subpart add/remove, and edit-mode
  pre-fill paths all still work as before.

## Next
After this PR lands the V2 M4 milestone is complete; the next session can
start M6-02 (retire the legacy `primary` blue token) and M5 (mobile pass).
