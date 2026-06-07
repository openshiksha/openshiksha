# Teacher Workspace — Initiative

> **North Star:** Authoring → assigning → monitoring is **one continuous,
> preview-driven flow** with no dead-ends and no lost context. From anywhere a
> teacher sees a problem set, they can preview exactly what students get, carry
> that selection straight into an assignment, edit it safely, publish, and then
> watch it land — without ever re-finding what they were just looking at.
>
> **Status:** 🟢 **Active** (promoted 2026-06-07, user-directed). The teacher
> dashboard rework ([#248](https://github.com/openshiksha/openshiksha/pull/248))
> fixed the worst breakage; this initiative makes the whole teacher surface
> coherent.

**Last updated:** 2026-06-07

---

## A. Why this initiative exists

The teacher surface grew feature-by-feature and the seams show. Concretely,
observed on the live app:

1. **Broken join code.** The "Generate join code" widget 404'd for every
   subject teacher, because the endpoint only authorized the homeroom
   `class_teacher` (which the demo classroom doesn't even set). Fixed in #248.
2. **Dead-end "Assign".** The dashboard's *Assign* buttons dropped the teacher
   on a blank `/teacher/assignments/new` with **nothing preselected** — the very
   problem set they clicked "Assign" on wasn't chosen. The flow lost its own
   context.
3. **No real preview before publish.** The Create-Assignment page showed a
   metadata card ("4 questions · ~20 min") but **not the actual questions a
   student would see**. A teacher published blind.
4. **Cluttered dashboard.** Every subject-room card eagerly mounted four
   data-fetching analytics panels — "many options but not much," in the user's
   words. Decluttered in #248.
5. **No path from preview to edit.** The read-only "preview as student" (#248)
   is great, but the obvious next move — *fix a typo right here* — has nowhere
   to go, and doing it unsafely would corrupt assigned work (that integrity
   problem is owned by the sibling
   [Authoring Integrity & Versioning](authoring-integrity-versioning.md)
   initiative).

Individually these are small; together they make the teacher surface feel
unfinished. This initiative treats the teacher workspace as **one product**, not
a pile of pages, and closes the seams in reviewable increments.

---

## B. Design principles

1. **Continuity of selection.** A thing you're looking at follows you into the
   next step. Click *Assign* on a set → that set is preselected. Click *Assign*
   on a room → that room is preselected.
2. **Preview before commit, everywhere.** Any time a teacher is about to give
   something to students, they can see the real, student-rendered thing first —
   not a summary.
3. **One render path for "what students see."** The student `QuestionCard` +
   student serializer is the single source of truth for previews (read-only),
   assignments, and the assignment page. No parallel preview renderer.
4. **Safe editing or no editing.** Inline editing of assigned content only ships
   on top of the snapshot/versioning guarantees from the Authoring Integrity
   initiative — never before.
5. **Lean by default, depth on demand.** Dashboard cards show identity + the one
   primary action; analytics and secondary tools live behind disclosures.
6. **No dead-ends.** Every empty state and every completed action offers the
   obvious next step.

---

## C. Backlog — TW-1 → TW-7 (lowest-risk-first)

### TW-1 — Assign continuity + preview-before-publish  *(shipping now)*
- Dashboard *Assign* buttons deep-link with `?problemSet=<id>` (from a set) or
  `?room=<id>` (from a room); `CreateAssignmentPage` reads them and preselects
  the room (and, for a set link, the matching subject room) and the set.
- A "Preview the actual questions as a student ↗" link in the assignment
  preview opens the read-only student render in a new tab — preview before
  publish, without losing the half-filled form.
- Builds on #248's read-only `ProblemSetPreviewPage` + fixed join code.
- **DoD:** clicking *Assign* on a set lands on a form with that set chosen and a
  one-click student preview; tests cover the preselection effects.

### TW-2 — Editable preview (depends on Authoring Integrity Phase 1)
- From the problem-set preview, let a teacher reorder / remove / add / edit
  questions inline (reusing the `CreateProblemSetPage` picker + widget gallery).
- **Blocked on** `AIV-1..3` (per-assignment content snapshot) so edits can't
  retroactively rewrite assigned/graded work. Tracked in
  [Authoring Integrity & Versioning](authoring-integrity-versioning.md).
- **DoD:** edit a set from preview; existing assignments provably unaffected.

### TW-3 — Assignment lifecycle view
- A teacher can open an assignment and edit due date, close / reopen it, and see
  per-student done/pending/overdue at a glance (some exists in
  `TeacherAssignmentDetailPage` — make it the hub).
- **DoD:** due-date edit + close/reopen persisted; roster status accurate.

### TW-4 — Dashboard information-architecture pass
- Tighten hierarchy: "needs attention" surfacing (overdue, ungraded, low
  completion) above the fold; consistent card grammar; guided empty states for
  a brand-new teacher (no rooms / no sets / no assignments).
- **DoD:** a first-run teacher always has a clear next action; a busy teacher
  sees what needs them first.

### TW-5 — Join-code UX
- Expiry display + regenerate with confirmation, copy + shareable link, optional
  QR for classroom projection. (Backend `ClassroomInviteCode` already supports
  `expires_at` / `is_active`.)
- **DoD:** a teacher can share a code three ways and see when it lapses.

### TW-6 — Question-bank ↔ authoring continuity
- From the question bank, "add to set" / "use in new set" without losing the
  search; from a set, jump to edit a question and come back.
- **DoD:** no context loss moving between bank, set builder, and question editor.

### TW-7 — Mobile teacher pass
- The teacher surfaces predate the mobile bottom-nav work; audit the authoring
  flows on a phone (the picker, the date input, the preview) and fix the rough
  edges.
- **DoD:** create-assignment and preview are usable one-handed on a phone.

**Suggested order:** TW-1 (now) → TW-3 ∥ TW-4 ∥ TW-5 (independent polish) →
TW-2 (after Authoring Integrity Phase 1) → TW-6 → TW-7.

---

## D. Definition of Done (North Star reached)

- From any problem set, a teacher can preview-as-student, carry it into an
  assignment with one click (preselected), preview the real questions again, and
  publish — no re-finding, no blind publish.
- Editing a set/question from preview is possible and **safe** (snapshots from
  the Authoring Integrity initiative protect assigned work).
- The dashboard shows what needs attention first and never dead-ends a teacher.
- Join codes work for every teacher and are easy to share.

---

## E. Relationship to other initiatives

- **[Authoring Integrity & Versioning](authoring-integrity-versioning.md)** —
  hard dependency for TW-2 (editable preview). That initiative owns the data
  model; this one owns the teacher UX on top of it.
- **Interactive Widgets** — the preview/edit surfaces must round-trip
  `widget_kind`/`widget_config` content.
- **Performance Budget** — the teacher pages are heavy (pickers, KaTeX preview);
  route-splitting them benefits both initiatives.

---

## F. Progress Ledger

| Date | Increment | PR | Notes |
|---|---|---|---|
| 2026-06-07 | Dashboard rework: fixed join code (subject-teacher auth + dedupe), read-only student preview, decluttered insights behind a disclosure, problem-sets section. | [#248](https://github.com/openshiksha/openshiksha/pull/248) | The breakage-fix slice. Motivated this initiative. |
| 2026-06-07 | **TW-1** — Assign continuity (`?problemSet=` / `?room=` deep links + preselection) + "preview actual questions as a student" link before publish. | _this PR_ | Closes the dead-end Assign flow and the blind-publish gap. Editable preview (TW-2) is deferred to after Authoring Integrity Phase 1 so edits stay safe. |
