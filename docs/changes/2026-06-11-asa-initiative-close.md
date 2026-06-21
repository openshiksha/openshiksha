# AI Surface Activation — endpoint map, DoD audit, initiative close

**Date:** 2026-06-11
**Classification:** Docs (initiative close)
**Initiative:** AI Surface Activation — final increment

## Summary

ASA-1..9 are all shipped, so this PR performs the close: the repeatable
endpoint-to-consumer map, the DoD audit against the North Star, and the
status flip to Done across the initiative doc, STATUS.md and the polish
backlog.

## What changed

- **`docs/ai-features/endpoint-consumer-map.md`** (new) — every
  `/api/v1/ai/` router registration mapped to its consumer, verified by grep
  on 2026-06-11: **17 endpoints directly consumed; 4 data-feeders consumed
  indirectly by design** (learning-gaps → interventions/drafts,
  misconceptions → clusters, mastery/knowledge-nodes → learning paths + SRS);
  **1 API-only** (`/ai/predictions/` — computed but unrendered, documented as
  a future product call). Includes a maintenance rule (update the map in the
  same PR that adds/consumes an endpoint) and the three conventions every
  consumer must follow (AIBadge provenance, 202+poll with visible progress,
  never error-as-empty-state).
- **`docs/initiatives/ai-surface-activation.md`** — status → ✅ Done; ASA-7
  marked shipped (#301 + #302); CI pool resolved (AIBadge #300, href sweep
  verified clean, endpoint map; `useAsyncGeneration` explicitly carried to
  maintenance — pure refactor of four tested call sites); new "DoD audit &
  close" section walking the three North-Star conditions; ledger rows for
  #299–#303 including the stacked-PR process lesson from the #294 orphan.
- **`docs/initiatives/STATUS.md`** — headline + table row → Done. No active
  initiative remains; candidate seeds noted (an `/ai/predictions/` teacher
  surface, Widget Studio discovery).
- **`docs/ai-features/polish-backlog.md`** — "Remaining gaps" updated: all
  four endpoint groups marked lit, `ExplanationPanel` badge bullet resolved
  (#300). Two minor cosmetic notes remain (cluster provenance model field,
  refresh confirmation linger) — recorded, not blocking.

## DoD audit result

1. No `/ai/` endpoint group without a frontend consumer — **met** (map).
2. Every AI surface passes the 8-point checklist — **met** (sweep complete
   #293/#294/#299; AIBadge #300; tested error paths throughout).
3. Recommendations → practice loop closes in one click — **met** (ASA-2
   #286; same principle extended to drafts→assignment and response→grade).

## Next steps

None for this initiative. Carried over: `useAsyncGeneration` extraction
(maintenance), `/ai/predictions/` surface (future initiative candidate).
