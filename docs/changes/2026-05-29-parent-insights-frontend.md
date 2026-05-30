# Parent Intelligence Dashboard — Frontend

**Date**: 2026-05-29
**Classification**: New (surfaces the backend shipped in PR #107)
**Branch**: `feat/2026-05-29-parent-insights-frontend` (based on `modernization`)

## Summary

Surfaces the Parent Intelligence Dashboard backend (`apps/ai` —
`ParentProgressSummary`, narrative + alerts + suggested home activities) as a
new `/parent/insights/:childId` page. Parents can read this week's narrative,
see urgent/attention/info alerts, work through suggested home activities, and
trigger an on-demand regeneration when no summary exists yet. A child-picker
landing route (`/parent/insights`) auto-redirects single-child parents to their
child's page; multi-child parents get a chooser. A "View Insights →" CTA was
added to each child's Overview header on the existing parent dashboard.

## What changed (frontend only — no backend churn)

- `useParentSummary.ts` — `useLatestParentSummary(childId)` (handles 404 →
  `null`) + `useGenerateParentSummary()` (invalidates `latest` on success).
  Local TypeScript interfaces mirror `ParentProgressSummarySerializer`.
- `components/NarrativeCard.tsx` — narrative paragraph, week range,
  `model_used` chip, plus a 4-tile stat row (questions, active days, avg
  score, week-over-week delta with semantic colour).
- `components/AlertsPanel.tsx` — severity-styled cards
  (urgent = red, attention = amber, info = blue), renders nothing on empty
  array (no "no alerts" filler).
- `components/HomeActivitiesPanel.tsx` — chapter/title/description cards
  with a celebratory emerald variant detected from the activity title.
- `ParentInsightsPage.tsx` — loading skeleton, success view, error retry,
  empty state with a primary "Generate this week's summary" CTA + a small
  "Regenerate" button in the success view. Refetches 1.5s after the
  `generate/` POST so eager-mode dev still picks up the new row.
- `ParentInsightsLandingPage.tsx` — child picker; 1-child parents are
  redirected immediately.
- `ParentDashboard.tsx` — new "View Insights →" entry-point beside each
  child's Overview header.
- Routes registered under the `PARENT` role guard:
  - `/parent/insights` → landing/picker
  - `/parent/insights/:childId` → insights page

## Decisions

- **Button, not third tab**, for the entry point on the parent dashboard
  — insights is a *destination page*, not another lens on the same
  proficiency chart.
- **404 → `null`, not error**: a parent with no summary yet is the
  expected first-visit state; the page renders an empty-state CTA in
  place of an error fallback.
- **Refetch on a 1.5s delay** after `generate/` POST: the endpoint returns
  `202` and queues a Celery task; in dev (`CELERY_TASK_ALWAYS_EAGER`) the
  row is ready by then; in prod the user can press "Regenerate" again if
  the first attempt was still in flight.
- **Celebrate-variant detection** is heuristic on the title rather than a
  new field (backend has no `kind` discriminator).

## Tests

- `AlertsPanel.test.tsx` — empty array renders nothing; severity attribute
  set per card.
- `HomeActivitiesPanel.test.tsx` — empty array renders nothing; title +
  description + chapter rendered; celebrate variant marked.

`tsc`, `eslint`, `vite build`, and the AI backend test suite (`pytest
openshiksha/apps/ai/`) all green.

## How to verify

1. Log in as a parent with at least one child.
2. Visit `/parent` — each child's Overview header now shows
   **View Insights →**.
3. Click it → land on `/parent/insights/<childId>`. With no existing
   summary, see the empty state. Click **Generate this week's summary**.
4. The page refetches; the narrative, alerts, and home-activity cards
   render with the deterministic stub summary even without an LLM key.
5. Visit `/parent/insights` directly — single-child parents are
   redirected; multi-child parents see a picker.

## Next steps

- Wire a Celery beat schedule for Monday-morning auto-generation (the
  task already exists — `generate_parent_progress_summary`).
- Pair the page with a Monday-morning email summary using the existing
  `emails.py` pipeline.
- i18n: expose an `en | hi` toggle on the page header once a global
  language switcher lands.
