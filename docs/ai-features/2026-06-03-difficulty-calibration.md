# Empirical Question Difficulty Calibration

**Category:** AI Question Generation (#2) — difficulty calibration from aggregate
student performance data
**Date:** 2026-06-03
**Status:** Implemented (backend + teacher dashboard panel)

## Problem it solves

Every question in OpenShiksha carries an **authored** difficulty (1–5) set by the
teacher who wrote it. That label is a guess until students actually answer the
question. Some "easy" questions stump the whole class; some "hard" ones everyone
aces; some are ambiguous or have a **mis-keyed correct answer** — and nobody
finds out unless a teacher manually trawls the gradebook.

This feature turns the existing grading stream into automatic **content quality
monitoring**. It's classic psychometric *item analysis*, computed entirely from
`Tick` records — **no LLM, no external infra**.

## How it works (technical)

For each `QuestionSubpart` attempted in a `SubjectRoom`, over that room's ticks:

- **Facility index** (`p`-value): the mean mark across attempts. High = easy,
  low = hard. A student who answers the same subpart several times (retries, SRS
  drills) contributes their *mean* mark, so one heavy practiser can't dominate.
- **Empirical difficulty** (1–5): the facility index mapped onto difficulty
  bands (`facility ≥ 0.85 → 1` … `< 0.30 → 5`).
- **Discrimination index**: top-third facility minus bottom-third facility, with
  students ranked by their *overall* mark in the room. Near-zero or negative
  means the item fails to separate strong from weak students — usually ambiguous
  wording or a wrong answer key. Left `null` when too few students to be stable.
- **Flag** — a single priority-resolved verdict:
  `TOO_HARD → TOO_EASY → LOW_DISCRIMINATION → MISLABELED → OK`. The facility
  extremes are checked before discrimination because a near-uniform item has
  ~zero discrimination *by construction* — there the "too easy/hard" story is the
  real one, not a keying problem.

Items attempted by fewer than 5 distinct students are skipped (too little signal).
Calibrations are a **refreshed-in-place snapshot**, not history: a recompute
deletes and replaces the room's rows, so stats that drift — or items no longer
attempted enough — update or disappear.

### Tunables (`apps/ai/analytics.py`)

| Constant | Default | Meaning |
|---|---|---|
| `CALIBRATION_MIN_STUDENTS` | 5 | Min distinct students before an item is calibrated |
| `DISCRIMINATION_MIN_STUDENTS` | 6 | Min students before discrimination is computed |
| `LOW_DISCRIMINATION_THRESHOLD` | 0.1 | Below this (incl. negative) → `LOW_DISCRIMINATION` |
| `TOO_EASY_FACILITY` | 0.95 | At/above → `TOO_EASY` |
| `TOO_HARD_FACILITY` | 0.10 | At/below → `TOO_HARD` |
| `MISLABEL_DELTA` | 2 | Empirical-vs-declared band gap that counts as mislabelled |

## Models / APIs created

**Model** — `QuestionDifficultyCalibration` (`ai_question_difficulty_calibrations`):
one row per `(subject_room, question_subpart)` holding `facility_index`,
`discrimination_index`, `empirical_difficulty`, `declared_difficulty`, `flag`,
`sample_size`, `attempt_count`, plus `difficulty_delta` / `needs_review`
properties. New `CalibrationFlag` text-choices enum.

**Engine** — `analytics.calibrate_subparts_for_subject_room(room)`,
`analytics.facility_to_difficulty(facility)`, `_discrimination_index(...)`,
`_calibration_flag(...)`.

**Task** — `tasks.refresh_difficulty_calibrations(subject_room_id)` (snapshot
replace, Celery).

**API** (teacher-only, all scoped to rooms the teacher owns):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/ai/difficulty-calibrations/` | List; `?subject_room=`, `?flag=`, `?needs_review=true` |
| GET | `/api/v1/ai/difficulty-calibrations/{id}/` | Single calibration |
| GET | `/api/v1/ai/difficulty-calibrations/summary/?subject_room=<id>` | Per-flag counts + totals |
| POST | `/api/v1/ai/difficulty-calibrations/refresh/` | Queue recompute (`{subject_room_id}`) |

**Admin** — `QuestionDifficultyCalibrationAdmin` (read-only, filter by flag/subject).

**Frontend** — `QuestionQualityPanel` on the Teacher Dashboard (V2 "Chalk &
Unlock" primitives): collapsible panel listing flagged questions with plain-
language hints, authored-vs-observed difficulty chips, discrimination, and a
Calibrate/Refresh button. Hooks in `useDifficultyCalibration.ts`.

## User impact

- **Teachers** get an at-a-glance "which of my questions are misbehaving?" list —
  a too-hard item to reword, a mis-keyed answer to fix, a too-easy item to
  retire — without reading the gradebook by hand.
- **Students** indirectly benefit from a cleaner, better-calibrated question bank.
- Difficulty labels become **self-correcting** over time as real data accrues.

## Tests

`apps/ai/tests/test_difficulty_calibration.py` (20 tests): facility→difficulty
band edges; empty room; min-sample drop; facility/empirical computation;
per-student averaging of repeat attempts; each flag (`too_easy`, `too_hard`,
`mislabeled`, `low_discrimination`); discrimination null below threshold; task
write + snapshot-replace; API list scoping, `needs_review` filter, summary
counts, refresh permissions (teacher-owned / unowned / student-forbidden).

Frontend: `tsc --noEmit` and ESLint clean.

## How to verify

1. Seed a room with ticks (or use `seed_demo_data`), then
   `POST /api/v1/ai/difficulty-calibrations/refresh/ {"subject_room_id": <id>}`.
2. `GET /api/v1/ai/difficulty-calibrations/?subject_room=<id>&needs_review=true`
   — flagged items appear with facility, discrimination, and verdict.
3. On the Teacher Dashboard, expand **Question Quality** under a subject room and
   hit **Calibrate**.

## Future enhancements

- Point-biserial correlation instead of the thirds split for discrimination.
- Cross-room (global) calibration as a property of the item itself, merging the
  per-room snapshots.
- Distractor analysis for MCQs (which wrong options are never / always chosen).
- Feed empirical difficulty back into the adaptive engine and assignment-draft
  difficulty targeting.
- Auto-suggest a corrected `difficulty` value the teacher can one-click accept.

## Dependencies

- `edge.Tick` (grading signal), `core.QuestionSubpart` / `core.Question`
  (`difficulty`), `core.SubjectRoom`. No external services.
