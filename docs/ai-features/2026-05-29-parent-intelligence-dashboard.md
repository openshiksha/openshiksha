# Parent Intelligence Dashboard

**Category:** Parent engagement & AI-summarised reporting
**Branch:** `ai/2026-05-29-parent-intelligence-dashboard`
**Status:** Backend complete; frontend follows in Phase 2 UI rebuild.

## Problem it solves

Parents on OpenShiksha currently see a basic dashboard with proficiency trends and assignment completion per child. That works for parents who already know the system, but most parents:

- Don't speak the language of "proficiency snapshots" or "tag-level scores"
- Don't have time to read tables — they want a clear *what does this mean* paragraph
- Aren't sure what to do at home to help their child
- Don't notice a slipping trend until it shows up in school grades

Teachers already get an AI-generated *weekly class report*. Parents deserve the same treatment for *their child*. This feature gives them one: a plain-language weekly progress summary, a short list of concrete activities they can do with their child at home, and a structured alerts list that flags things worth their attention (sharp drop, severe gap, inactive for a week).

## How it works

Once a week — or on demand from the API — the system:

1. **Computes a deterministic stats snapshot** for the child over the Mon→Sun window:
   - Ticks recorded, distinct days active, average tick mark
   - Score delta vs the prior week (positive = improving)
   - Top weak chapters (avg < 50%) and strong chapters (avg ≥ 60%)
   - Active subjects, days since last tick
2. **Generates a plain-language narrative** via the LLM cascade
   (Claude → Google Gemma → Ollama → deterministic stub). The stub guarantees
   the page renders even if no LLM provider is configured.
3. **Derives suggested home activities** heuristically from the weak chapters
   ("Spend 15 minutes on Long Division — ask Aanya to explain each step"),
   falling back to a celebration of the strongest chapter when there are no
   weak chapters yet.
4. **Derives parent alerts** purely from the stats (no LLM): no-practice,
   inactive 7+ days, sharp score drop (urgent), severe gap (urgent),
   strong improvement (info).
5. **Upserts a `ParentProgressSummary`** keyed on `(parent, child, week_start)`,
   so re-running for the same week overwrites in place.

The whole pipeline is idempotent and self-contained — no other AI feature
needs to change.

## Models, APIs, tasks

### Model
`openshiksha.apps.ai.models.ParentProgressSummary`
  - FKs: `parent` (role=parent), `child` (role=student/open_student)
  - Stats: `ticks_recorded`, `active_days`, `avg_score`, `score_delta`,
    `weak_chapters` (JSON), `strong_chapters` (JSON)
  - Narrative: `summary_text`, `language` (en/hi)
  - Generated content: `home_activities` (JSON), `alerts` (JSON)
  - Provider metadata: `model_used`, `input_tokens`, `output_tokens`
  - `unique_together = (parent, child, week_start)`
  - Property: `has_urgent_alert`

`ParentAlertSeverity` TextChoices: `info`, `attention`, `urgent`.

### Analytics functions
`openshiksha.apps.ai.analytics`
  - `compute_parent_weekly_stats(child, week_start, week_end) -> dict`
  - `build_home_activities(stats) -> list[dict]`
  - `build_parent_alerts(stats) -> list[dict]`

### LLM client
`openshiksha.apps.ai.llm_client.generate_parent_summary(stats, language="en")`
  uses the same provider cascade as `generate_class_summary`.

### Celery task
`openshiksha.apps.ai.tasks.generate_parent_progress_summary(parent_id, child_id, week_start_iso=None, language="en")`
  - Validates the parent-child link via `User.children`
  - Defaults to the current week's Monday; explicit dates snap back to Monday
  - Idempotent upsert keyed on `(parent, child, week_start)`

### REST API (parent-only)
- `GET    /api/v1/ai/parent-summaries/`                  — summaries for all the parent's children
- `GET    /api/v1/ai/parent-summaries/?child=<id>`       — filter to one child
- `GET    /api/v1/ai/parent-summaries/{id}/`             — one summary
- `GET    /api/v1/ai/parent-summaries/latest/?child=<id>` — most recent summary for one child
- `POST   /api/v1/ai/parent-summaries/generate/`         — queue generation, body `{child_id, week_start?, language?}`

Permissions: only `role=parent`, and only for children linked via `User.children`.
Students, teachers and the wrong parent all see nothing / get 403 on generate.

### Admin
`ParentProgressSummaryAdmin` registered with list filters on week / language /
model, search across parent and child usernames + narrative text.

## User impact

- **Parents** get a *narrative they can actually read*. "Aanya practised on 4
  days this week and improved 12% in Algebra; she still finds Long Division
  hard — try 15 minutes together on it before the weekend." That is much more
  useful than a proficiency chart.
- **Parents** get **alerts** for the moments that matter (no practice in
  10 days, sharp drop, severe gap) — they no longer need to babysit the dashboard.
- **Parents** get **concrete home activities** they can do *with* the child —
  a measurable improvement over "your child needs more practice."
- **Students** benefit indirectly: parents who feel informed are more likely
  to support the right kind of practice rather than blanket pressure.

## Future enhancements

- Schedule a Celery beat job to auto-generate Monday-morning summaries for
  every parent without requiring an explicit POST.
- Email the previous week's summary every Monday (extends the existing
  email-notifications pipeline).
- Track parent engagement with the home activities (did they tap "mark done"?)
  and feed that signal back into the recommendation engine.
- Group summaries across multiple children for parents with several kids on
  the platform.
- Frontend: a dedicated `/parent/insights` page that pairs the narrative with
  the existing proficiency-trends chart and assignment-completion view from
  the Phase 1 parent dashboard.

## Dependencies

- Builds on existing `core.User.children` M2M (no schema change there)
- Reuses `Tick` data — no new ingestion path
- Reuses `llm_client._call_anthropic_text` / `_call_google_gemma` / `_call_ollama`
- Migration: `ai/0007_parent_progress_summaries.py` (single `CreateModel`)
- Adds one Celery task and one DRF viewset; no impact on existing AI features
