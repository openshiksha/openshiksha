# Manual test — Route-level mobile layouts (Batch 4)

**Date:** 2026-06-18
**Covers:** RML-1..4 (#382–#385) — dense teacher surfaces made readable on a phone.

These are pure responsive-layout changes behind the Tailwind `sm:` breakpoint
(640 px). Verify in Chrome DevTools **device toolbar** at a phone width
(**360–390 px**, e.g. "iPhone SE" / a 360 px custom width) and again at a desktop
width to confirm the desktop layout is unchanged.

## How to run

```bash
cd frontend_modern && npm run dev
```

Log in as a **teacher** (the affected surfaces are all teacher routes). Open
DevTools → toggle the device toolbar → set the viewport to 360 px wide.

## Acceptance — for every surface below

- [ ] **No horizontal scroll** at 360 px (the page never scrolls sideways; no
      pinch-zoom needed).
- [ ] **Every column / field is legible** — nothing clipped or truncated to
      illegibility.
- [ ] **Touch targets ≥ 44 px** for interactive controls (tabs, buttons, inputs).
- [ ] At `≥ sm` (≥ 640 px) the surface looks **identical to before** (these are
      refactors, not redesigns).

## Surfaces

### 1. Class Health (RML-1) — `ResponsiveTable`

- Teacher dashboard → a subject-room card → expand **"Class Health"** (needs
  class-insight data; trigger from the panel if empty).
- [ ] At 360 px the Chapter / Avg / Struggling / Status table renders as a
      **stacked card list** — chapter name as the card heading, the other three as
      label/value rows. No horizontal scroll.
- [ ] At ≥ 640 px it is the **original 4-column table** (header row, hover, status
      dot + label).
- [ ] The `/design` route → "Responsive table" section shows the same swap as you
      cross 640 px.

### 2. Assignment-detail submissions (RML-2)

- Teacher dashboard → an assignment → **"Student Submissions"**.
- [ ] At 360 px each submission is a **card**: student name heading, then
      Submitted / Score / Status as label/value rows. No horizontal scroll.
- [ ] At ≥ 640 px it is the original Student / Submitted / Score / Status table.
- [ ] Score badge colours (green ≥70 / amber ≥40 / rose) and the ✓ Submitted /
      ⏳ Pending status pills are preserved.
- [ ] **Localization:** switch the language to **हिं** — the page heading
      ("छात्रों के सबमिशन"), stat labels, badges, and dates all render in Hindi
      (this page previously had hardcoded English).

### 3. Create-Question form (RML-3)

- Teacher → **Create Question** (`/teacher/questions/new`).
- [ ] At 360 px the AI-panel **Type / Difficulty / Count** selectors stack into
      one column per row (not three squeezed columns).
- [ ] The **Subject / Standard** chapter selectors stack into one column per row.
- [ ] The subpart **tab strip** scrolls horizontally and each tab is ≥ 44 px tall
      / easily tappable.
- [ ] The KaTeX preview sits **below** the question-text input (single column).

### 4. Open-Response grading (RML-4)

- Teacher → **Open-response grading** queue → an `ai_graded` item.
- [ ] At 360 px the review form's **Final marks** input and **Comment** field
      stack into one full-width column each (not crowded side-by-side).
- [ ] The Accept / Save button is full-width-reachable and the AI provenance row
      (`✨ AI-generated` badge, confidence) is not clipped.
- [ ] A very long student response **wraps** inside the blockquote (no horizontal
      scroll from an unbroken token).

## Notes

- No backend, no new dependency, no schema change — frontend-only.
- Every PR ran `npm run test` / `tsc --noEmit` / `eslint` / `npm run build`; the
  entry chunk is unchanged against the 160 kB CI guard (the `ResponsiveTable`
  primitive is tiny and imported only into already-lazy teacher routes).
