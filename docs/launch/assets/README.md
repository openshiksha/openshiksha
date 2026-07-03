# Launch video — reference stills

First-pass frames for judging the [video plan](../video-plan.md) script against
real UI. These are **reference/rehearsal stills, not the final recording** — the
launch video is captured live on the running stack.

They are regenerated reproducibly (no manual dev-stack run) by the backend-free
Playwright spec [`frontend_modern/e2e/launch-stills.spec.ts`](../../../frontend_modern/e2e/launch-stills.spec.ts),
which drives the public `/widgets/dev` playground — same mechanics as the
golden-path demo stills. Regenerate with:

```bash
cd frontend_modern
npx playwright test launch-stills
```

| File | Shot | Frame |
|---|---|---|
| `shot-01-describe-to-build.png` | Shot 1 | Number line (axis 0–1, snap ½), student marks ½ → host reads `0.5` |
| `shot-05-step-solver.png` | Shot 5 | `2x + 1 = 7` solved line by line (`2x = 6` ✓, `x = 3` ✓) → host reads `"x = 3"` |

**Not yet captured — needs the seeded full stack (auth + `seed_demo_data`):**

- **Shot 4** (student drags a point inside a *real* assignment → graded). The
  playground frame above (shot 1) already shows the same number-line widget
  drag→report interaction backend-free; the assignment-detail framing is
  deferred to a stack-up QA pass once the demo seed is live (T-1 / #503).
