# Initiatives — long-horizon work that compounds across sessions

OpenShiksha ships in **small daily increments** (one routine session → one focused
PR + a change doc). That cadence is great for momentum but naturally **myopic**:
each session optimises for "what's a good thing to ship *today*," and large,
multi-session goals never get the sustained, coherent investment they need.

**Initiatives** fix that. An initiative is a long-horizon goal (the V2 design
overhaul, a mobile shell, an AI tutor, an accessibility pass) that is too big for
one session but can be **advanced one increment per session** and **improved over
time** rather than built once and abandoned.

This folder is the durable home for those goals. Any routine — feature, AI,
infra, design — can open this folder, pick up the top initiative, and move it
forward without re-deriving the whole plan.

---

## How a routine uses initiatives (read this every session)

When a session has no higher-priority, time-sensitive work, **advance an
initiative** instead of inventing a one-off task:

1. **Pick.** Open [`STATUS.md`](STATUS.md). Take the **highest-priority active
   initiative**. Inside its doc, take the **top unblocked increment** from its
   Backlog.
2. **Build it to the bar.** Implement exactly that increment — no more (avoid
   scope creep) and no less (meet the increment's Definition of Done). One
   increment ≈ one reviewable PR, the same size this repo ships daily.
3. **Harden the foundation (the compounding step).** Before finishing, do **one
   small system-improvement task** from the initiative's "Continuous Improvement"
   list — refine a token, delete a duplication, fix an a11y gap, tighten a
   convention, add a missing showcase entry. This is what makes the system get
   *better* over time, not just *bigger*.
4. **Record.** Update the initiative's **Progress Ledger** (increment → done, PR
   link, date, one-line learning) and tick the Backlog item. Update
   [`STATUS.md`](STATUS.md) if the initiative's headline progress changed.
5. **Write the change doc** as usual in `docs/changes/`, and link the initiative.

If an increment turns out bigger than one session, **split it** in the Backlog
and ship the first slice — never leave the tree broken.

---

## Rules that keep multi-session work coherent

- **One source of truth per initiative.** The initiative doc owns its design
  language, conventions, backlog, and ledger. Don't fork decisions into daily
  plans; link back here.
- **Conventions over taste.** Each initiative defines conventions (tokens, file
  layout, naming). Follow them even if you'd personally do it differently — 30
  sessions following one convention beat 30 sessions of personal style.
- **Definition of Done is non-negotiable.** Every increment meets the
  initiative's quality bar (build/tests/lint/types green, responsive, accessible,
  token-only, showcased, ledgered). A half-done increment is worse than none.
- **Leave it better.** Every session does step 3. The foundation should be
  cleaner at the end of a session than at the start.
- **Make progress visible.** Prefer increments that add to a living, viewable
  surface (e.g. the `/design` showcase) so humans can see the system maturing.

---

## Anatomy of an initiative doc

Each `docs/initiatives/<id>.md` contains, in this order:

| Section | Purpose |
|---|---|
| **North Star** | The one-paragraph vision + who it's for + the tone. |
| **Principles** | The non-negotiable design/architecture beliefs. |
| **Foundation / Scaffold** | What already exists for a session to build on. |
| **Backlog** | Prioritised, **session-sized** increments, each with a DoD. |
| **Definition of Done** | The quality bar every increment must clear. |
| **Continuous Improvement** | The pool of "harden the foundation" tasks (step 3). |
| **Progress Ledger** | Append-only log: increment, date, PR, learning. |

---

## Active initiatives

See [`STATUS.md`](STATUS.md) for the live priority order and headline progress.

There is no active initiative at the moment. The previous top initiative,
[`interactive-widgets-framework.md`](interactive-widgets-framework.md), is
paused after IW-8: configure/code widgets are shipped, while Widget Studio is
deferred pending product validation.

---

## Starting a new initiative

Copy the anatomy above into `docs/initiatives/<year>-<slug>.md`, write the North
Star / Principles / first Backlog, add a row to `STATUS.md`, and link it from the
"Active initiatives" list here. Keep the first Backlog short and concrete — it
will grow as the work teaches you what's needed.
