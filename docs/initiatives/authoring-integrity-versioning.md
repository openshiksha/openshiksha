# Authoring Integrity & Versioning — Initiative

> **North Star:** A teacher can **preview, edit, and add to** problem sets and
> assignments with confidence — and an edit **never silently rewrites work that
> is already assigned or already graded.** What a student was given, and what
> they were graded against, is immutable history. The live, editable copy and
> the assigned, frozen copy are clearly separate, and moving changes from one to
> the other is an explicit, reviewable act.
>
> **Status:** 🟢 **Active** — Phase 1 (AIV-1..3) **done 2026-06-08** across
> [#270](https://github.com/openshiksha/openshiksha/pull/270)–[#274](https://github.com/openshiksha/openshiksha/pull/274).
> Silent-data-corruption hole is closed; TW-2 (editable preview) is unblocked.
> Next bet is **Phase 2** (AIV-4 + AIV-5) — editable + assignment-level preview
> that renders from the snapshot.

**Last updated:** 2026-06-08

---

## A. Why this initiative exists

The teacher-dashboard rework ([#248](https://github.com/openshiksha/openshiksha/pull/248))
added a **read-only** "preview as student" for problem sets. The natural next
ask is an **editable** preview — tweak a question, add one, fix an answer, right
from where you're reviewing the set. But the moment editing enters the picture,
a latent data-integrity bug becomes a real one.

**The problem, concretely** (verified in the code):

- `Assignment.problem_set` is a **live FK** to `ProblemSet`
  ([models.py](../../backend/openshiksha/apps/core/models.py)).
- `ProblemSet.questions` is a **mutable M2M**; `add-question` already mutates it
  in place.
- `grade_submission` reads the **live** set and the **live**
  `QuestionSubpart.correct_answer` at grade time
  ([tasks.py:48-89](../../backend/openshiksha/apps/core/tasks.py)).
- `Submission.answers` is keyed by **live subpart id**.

So today, if a teacher edits a set or a question **after** it's been assigned:

1. **Add/remove a question** → every existing assignment using that set silently
   gains/loses a question. A student mid-attempt sees the question list change;
   a re-grade uses the new list.
2. **Edit a question's text or correct answer** → the "right" answer changes
   **retroactively** for every past submission. A student who was correct can
   become wrong on re-grade, with no record of what they were actually asked.
3. **Shared content blast radius** — `ProblemSet.school = null` and shared
   `Question`s are used across *every* school. One teacher's edit changes other
   schools' assigned material.

There is **no snapshot, no version, no lock** anywhere in the chain. The only
thing standing between "fix a typo" and "silently re-grade 400 students' graded
work" is that the UI doesn't yet expose editing from the preview. This
initiative builds the safety model **before** we expand that editing surface.

---

## B. Design principles

1. **Assigned content is immutable history.** Once a `ProblemSet` is assigned,
   what that assignment contains — questions, text, options, correct answers —
   is frozen for that assignment. Grading reads the frozen copy, never the live
   one.
2. **Edit the working copy freely.** The live `ProblemSet` / `Question` is a
   teacher's working draft. Editing it is cheap and unscary precisely because it
   can't reach back into assigned work.
3. **Promotion is explicit.** Pushing edits into an existing assignment (or
   re-grading against new content) is a deliberate, confirmed action with the
   blast radius shown ("this re-grades 31 submitted answers"). Never a
   side-effect of saving.
4. **Snapshot first, version later.** The cheapest fix that removes the bug is a
   per-assignment content snapshot. Full version history is a richer follow-on,
   not a prerequisite.
5. **No new grading path.** Grading still runs through `grade_submission`; it
   just sources content from the snapshot. One grader, one code path.
6. **Backwards-compatible migration.** Existing assignments get a snapshot
   backfilled from their current live content (the best available truth) so
   nothing breaks on deploy.

---

## C. Approaches considered

| Approach | Integrity | Dedup / storage | Complexity | Verdict |
|---|---|---|---|---|
| **A. Copy-on-assign snapshot** — freeze the set's question content into the assignment at assign time | ✅ full | ❌ duplicates content per assignment | 🟢 low | **Phase 1 foundation** |
| **B. Versioned problem sets** — immutable `ProblemSetVersion`; assignment pins a version; edit = new draft → publish | ✅ full | ✅ shared immutable versions | 🟡 medium | **Phase 3 (the real model)** |
| **C. Full question + set versioning** — every `Question` is versioned too; assignment pins the whole graph | ✅ full | ✅ | 🔴 high | Overkill for now; revisit if content reuse demands it |

**Chosen path:** ship **A first** (kills the bug fast, unblocks editable
preview), then evolve toward **B** for storage efficiency, an update path, and
audit history. A is a strict subset of B's guarantees, so it's not throwaway —
the snapshot becomes "version pinned at assign time" once versions exist.

---

## D. Backlog — AIV-1 → AIV-8 (phased, lowest-risk-first)

### Phase 1 — Snapshot integrity (removes the bug)

#### AIV-1 — Assignment content snapshot model + backfill *(do first; foundation)*
- **Backend:** new `AssignmentSnapshot` (or `assigned_content` JSONField on
  `Assignment`) capturing, at assign time, the ordered list of questions with
  their subparts' `question_text`, `options`, `correct_answer`,
  `subpart_type`, `variable_constraints`, `widget_kind`/`widget_config`, and
  image/solution/hint text — everything the renderer + grader need.
- **Capture** in `perform_create` of the assignment (and the remedial
  auto-creation path in `_create_remedial_assignment`).
- **Migration** backfills every existing assignment from its current live set
  (best-available truth, logged as "backfilled").
- **DoD:** every assignment has a snapshot; creating an assignment freezes
  content; editing the live set afterward leaves the snapshot byte-identical.

#### AIV-2 — Grade + serve from the snapshot
- **Backend:** `grade_submission` reads subpart content (correct answers,
  types, constraints) from the assignment snapshot, not `problem_set.questions`.
  The student assignment serializer (`AssignmentDetailSerializer` /
  `ProblemSetStudentDetailSerializer` path) renders from the snapshot too, so a
  student always sees exactly what was assigned.
- **DoD:** a golden test — assign a set, submit, edit the live set's correct
  answer, re-grade → score is **unchanged** (graded against the snapshot). The
  same edit on a *new* assignment grades against the new answer.

#### AIV-3 — Edit-safety guardrails + signals in the UI
- **Backend:** lightweight read-only flags on the set/question serializers:
  `assigned_count`, `has_graded_submissions`. (Snapshots already protect
  integrity; these drive UX, not safety.)
- **Frontend:** when a teacher edits a `Question` or set that's already
  assigned, show a non-blocking notice: *"This is used in N assignments. Your
  edits apply to **future** assignments; existing ones keep what students were
  given."* — turning a silent footgun into an understood, safe action.
- **DoD:** editing assigned content shows the notice; nothing is blocked;
  integrity is already guaranteed by AIV-1/2.

### Phase 2 — Editable preview (the feature the user asked for)

#### AIV-4 — Editable problem-set preview
- Extend `ProblemSetPreviewPage` (or a sibling authoring view) so a teacher can,
  from the preview: reorder, remove, add (reuse `WidgetGalleryPanel` /
  question-picker from `CreateProblemSetPage`), and jump to edit a question.
- Edits hit the **live** set via existing endpoints (`add-question`, set
  update, question edit). Because of Phase 1, this is safe by construction.
- **DoD:** a teacher edits a set from preview; assignments already made from it
  are provably unaffected (snapshot test); the live set reflects the edits.

#### AIV-5 — Assignment-level preview + "what students see now"
- A teacher opening an assignment can preview the **snapshot** (what was
  actually assigned) distinctly from the **current live set** (what a new
  assignment would contain), with a clear diff/affordance when they differ.
- **DoD:** assignment preview renders the frozen snapshot; a banner appears when
  the live set has drifted from the snapshot, linking to AIV-6.

### Phase 3 — Versioning + promotion (the durable model)

#### AIV-6 — "Update this assignment to the latest content" (guarded re-sync)
- An explicit action that re-snapshots an assignment from the current live set,
  showing the blast radius first (*"adds 1 question, changes 2 answers;
  re-grades 31 submitted answers"*) and offering re-grade.
- **DoD:** re-sync is opt-in, previewed, reversible (keeps prior snapshot in
  history), and triggers re-grade only on confirm.

#### AIV-7 — `ProblemSetVersion` (publish/draft) — migrate snapshots → versions
- Introduce immutable `ProblemSetVersion` rows; assignment pins a version
  instead of carrying a private snapshot (dedup). Editing a published set
  creates a new draft; "Publish" mints a version. Backfill: each existing
  snapshot becomes a version.
- **DoD:** assignments reference versions; identical content shares one version;
  editing never mutates a published version.

#### AIV-8 — Version history + audit UI
- A teacher can see a set's version history, diff two versions, and see which
  assignments pin which version. Optional: question-level pinning (Approach C)
  if shared-question edits prove to need it.

**Suggested order:** AIV-1 → AIV-2 → AIV-3 (Phase 1 closes the integrity hole)
→ AIV-4 ∥ AIV-5 (the editable preview the user wants, now safe) → AIV-6 → AIV-7
→ AIV-8. **Phase 1 is shippable on its own and is the priority** — it removes a
real silent-data-corruption risk even if editable preview never ships.

---

## E. Definition of Done (North Star reached)

- Editing a problem set or question **never** alters the content or grade of an
  assignment that already exists; a regression test proves it.
- A teacher can preview, edit, add to, and reorder a set from one surface, and
  understands (via clear UI) that edits apply to future assignments.
- Re-syncing an existing assignment to new content is explicit, previews its
  blast radius, and re-grades only on confirmation.
- Assignments pin an immutable content version; version history is auditable.
- Shared (`school=null`) content edits can't retroactively change another
  school's assigned material.

---

## F. Risks & open questions

- **Storage of snapshots** (Phase 1) duplicates content per assignment;
  acceptable short-term, resolved by AIV-7's shared versions.
- **In-progress submissions** when content changes: snapshots make this a
  non-issue for *existing* assignments; confirm the student app reads the
  snapshot for the whole attempt lifecycle.
- **Remedials** (`ProblemSet.is_remedial`, `source_assignment`) auto-create sets
  from graded mistakes — ensure they snapshot at creation like any assignment.
- **Variable substitution / croupier** is seeded per `(student_id, subpart_id)`;
  snapshots must keep stable subpart ids (or carry the seed) so a re-grade is
  deterministic.
- **Widget configs** (`widget_kind`/`widget_config`) are content too — include
  them in the snapshot.

---

## G. Relationship to other initiatives

- **Teacher-dashboard rework ([#248](https://github.com/openshiksha/openshiksha/pull/248))**
  shipped the read-only preview that motivates this; AIV-4 turns it editable.
- **Interactive Widgets** — widget config is snapshotted content; this
  initiative must round-trip `widget_kind`/`widget_config` through snapshots.
- **Cabinet Data Fidelity** — the imported 646-question corpus is the shared
  content whose edits have cross-school blast radius; versioning protects it.

---

## H. Progress Ledger

| Date | Increment | PR | Notes |
|---|---|---|---|
| 2026-06-07 | Initiative drafted (⚪ Proposed). Root-caused the live-content grading risk; chose snapshot-first (Approach A) → versioning (Approach B). | _(this docs PR)_ | Motivated by the editable-preview ask on [#248](https://github.com/openshiksha/openshiksha/pull/248). Phase 1 (AIV-1..3) is independently shippable and is the priority — it removes a silent data-corruption risk. |
| 2026-06-08 | **Promoted to top initiative (🟢 Active).** Planned Phase 1 as a 5-PR batch: AIV-1 (snapshot model + capture in both creation paths + backfill) → AIV-2a (grade from snapshot + golden test) ∥ AIV-2b (serve snapshot to student) ∥ AIV-3a (edit-safety flags) → AIV-3b (edit-safety UI notice). | _(plan: [docs/daily-plans/2026-06-08-plan.md](../daily-plans/2026-06-08-plan.md))_ | Only unblocked next bet; gates TW-2. Re-confirmed in code: `grade_submission` reads live content ([tasks.py:52,84](../../backend/openshiksha/apps/core/tasks.py)); two creation paths to instrument — `AssignmentViewSet.perform_create` and `_create_remedial_assignment`. |
| 2026-06-08 | **AIV-1 done** — `Assignment.assigned_content` JSONField, `apps.core.snapshots.build_assignment_snapshot()`, captured in both creation paths (`AssignmentSerializer.create` + `_create_remedial_assignment`), backfilled every existing assignment from its live set. Byte-identical-after-live-edit regression test pins the integrity invariant. | [#270](https://github.com/openshiksha/openshiksha/pull/270) | Zero behaviour change on its own — readers still hit the live set. Foundation for AIV-2a/2b. |
| 2026-06-08 | **AIV-2a done** — `grade_submission` reads `subpart_type`, `correct_answer`, `variable_constraints` from the assignment snapshot; falls back to the live set only for legacy rows the backfill couldn't reach. Ships the **golden regression test** (edit live `correct_answer` → re-grade unchanged) + per-assignment corollary (a new assignment after the same edit grades against the new answer). | [#271](https://github.com/openshiksha/openshiksha/pull/271) | The silent-corruption hole is closed at the grader. |
| 2026-06-08 | **AIV-2b done** — student assignment-detail serializer (`AssignmentDetailSerializer.to_representation`) renders `problem_set.questions` from the snapshot via `render_snapshot_for_student`. Same croupier shuffle + `{{var}}` substitution as the live path; response shape preserved 1:1; no `correct_answer` leak. | [#272](https://github.com/openshiksha/openshiksha/pull/272) | Student sees exactly what they were assigned, even after the live set drifts. |
| 2026-06-08 | **AIV-3a done** — read-only `assigned_count` + `has_graded_submissions` flags on `ProblemSetSerializer` + `QuestionSerializer`, backed by `Count` + `Exists` annotations so list endpoints stay N+1-free. Falls back to per-row query when annotation absent (POST responses). | [#273](https://github.com/openshiksha/openshiksha/pull/273) | UX-only signal — integrity is guaranteed by AIV-1/2; this just makes "edit is future-only" legible to the editor. |
| 2026-06-08 | **AIV-3b done** — non-blocking edit-safety banner on `CreateQuestionPage` in edit mode. Says "this question is used in N assignment(s); edits apply to future assignments only" with stronger wording when graded submissions exist. Nothing is disabled. | [#274](https://github.com/openshiksha/openshiksha/pull/274) | Closes Phase 1's Definition of Done. ProblemSet edit surface will reuse the same component when TW-2 ships. |
| 2026-06-08 | **Phase 1 closed.** Silent-data-corruption hole is gone; TW-2 (editable preview) is unblocked. Teacher Workspace promoted back to Active. Next bet: **Phase 2** (AIV-4 editable + AIV-5 assignment-level preview rendering from the snapshot). | — | All five PRs landed clean. |
