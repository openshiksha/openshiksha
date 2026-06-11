# /ai/ Endpoint → Consumer Map

The repeatable version of the audit that seeded the AI Surface Activation
initiative (2026-06-09): every `/api/v1/ai/` router registration
(`backend/openshiksha/apps/ai/urls.py`) and where its data reaches a user.

**Maintenance rule:** when you add or consume an `/ai/` endpoint, update this
table in the same PR. Re-verify with:

```bash
cd frontend_modern/src
grep -rl "ai/<endpoint>" --include="*.ts" --include="*.tsx" . | grep -v test
```

Last verified: **2026-06-11** (ASA close).

## Directly consumed

| Endpoint | Frontend consumer | Surface |
|---|---|---|
| `/ai/recommendations/` | `student/useRecommendations.ts` → `RecommendationsPanel` | Student dashboard "What to Practice Next" (click-through to chapter practice, ASA-2) |
| `/ai/practice-plans/` | `student/usePracticePlan.ts` | Student practice plan |
| `/ai/class-insights/` | `teacher/useClassInsights.ts` → `ClassHealthPanel` | Teacher room insights |
| `/ai/trigger/` | `teacher/ClassHealthPanel.tsx` | Recompute trigger from the class health panel |
| `/ai/spaced-repetition/` | `student/useSpacedRepetitionDue.ts`, `useSRSDrill.ts` → `DueForReviewPanel`, `SRSDrillPage` | SRS due list + drill (server-side same-day guard, ASA-9) |
| `/ai/learning-paths/` | `student/useLearningPaths.ts` → `LearningPathPage` | Student learning path |
| `/ai/explanations/` | `student/useExplanation.ts` → `ExplanationPanel` (assignments via `QuestionCard`, drill via `SRSDrillPage`) | Post-submit "Explain this answer" (ASA-4, ASA-8) |
| `/ai/generate-questions/` | `teacher/useGenerateQuestions.ts` → `AIGenerationPanel` | Question authoring AI drafts |
| `/ai/weekly-reports/` | `teacher/useWeeklyReport.ts` → `WeeklyReportPanel` | Teacher weekly class summary |
| `/ai/hints/` | `student/useHints.ts` → `AIHintPanel` (in `QuestionCard`) | Per-subpart hints during practice |
| `/ai/misconception-clusters/` | `teacher/useMisconceptionClusters.ts` → `MisconceptionClustersPanel` | Class misconception patterns (ASA-5) |
| `/ai/parent-summaries/` | `parent/useParentSummary.ts` → `NarrativeCard` / `ParentInsightsPage` | Parent weekly narrative |
| `/ai/assignment-drafts/` | `teacher/useAssignmentDrafts.ts` → `AssignmentDraftsPanel` | AI assignment drafts: generate → review → approve/dismiss (ASA-6) |
| `/ai/open-grades/` | `teacher/useOpenResponseGrading.ts` → `OpenResponseGradingPage` | Open-response grading queue: AI suggests, teacher finalises (ASA-7a) |
| `/ai/open-rubrics/` | `teacher/useOpenRubrics.ts` → `RecordResponsePanel` (on the grading page) | Rubric authoring per short-answer subpart (ASA-7b) |
| `/ai/interventions/` | `teacher/useInterventions.ts` → `InterventionsPanel` | Per-student intervention strategies |
| `/ai/difficulty-calibrations/` | `teacher/useDifficultyCalibration.ts` | Empirical difficulty calibration |

## Consumed indirectly (data feeders — no direct frontend fetch, by design)

| Endpoint | Where its data reaches users |
|---|---|
| `/ai/learning-gaps/` | Feeds `InterventionSuggestion` (focus chapters/severity) and `AssignmentDraft` targeting (`tasks.py`); gap data surfaces through those panels |
| `/ai/misconceptions/` | Per-student rows aggregated into `/ai/misconception-clusters/` (the cluster panel is the user surface); labels also appear on intervention cards |
| `/ai/mastery/` | Mastery records drive `/ai/learning-paths/` and SRS scheduling (`tasks.py`) |
| `/ai/knowledge-nodes/` | Taxonomy behind mastery/SRS/learning paths |

## API-only (no user surface yet — candidates for a future initiative)

| Endpoint | Status |
|---|---|
| `/ai/predictions/` | `PerformancePrediction` rows are computed (`tasks.py`) but no panel renders them. Deliberately left out of ASA scope (the audit's four dark *groups* are all lit); a "predicted outcome" teacher surface is a future product call, not a wiring gap. |

## Conventions every consumer must follow

- **Provenance:** `<AIBadge modelUsed stubLabel>` from `@/shared/ui` —
  never a hand-rolled badge (`docs/initiatives/ai-surface-activation.md`,
  principle 3).
- **Async generation:** 202 + poll with a visible working state and a retry
  path; stop polling when nothing is pending.
- **List errors:** an error must never render as an empty state
  (the 2026-06-10 sweep — see `polish-backlog.md`).
