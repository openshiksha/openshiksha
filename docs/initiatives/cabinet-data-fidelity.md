# Cabinet Data Fidelity — Top Initiative (M7-03 → M7-09)

> **Status (2026-05-30 audit)**: 644 imported questions, 1734 subparts. After
> the M7-02 substitution + image fix, the content *substitutes* correctly,
> but the **structural fidelity** of the imported data is still poor —
> compound questions render the wrong input widget, raw HTML markup leaks
> through, LaTeX environments don't typeset, and most images aren't
> attached. The student surface is functional but unsalvageable on real
> content until this initiative ships.
>
> Per user direction 2026-05-30: this **replaces** the previous
> "M7-03 filter/search/sort" and "M4-01 Student Dashboard" as the top next
> session, and stays #1 until every issue below is closed.

---

## A. The audit (run 2026-05-30 against modernization + M7-02 fix branch)

| Concern | Affected | Symptom in UI |
|---|---:|---|
| Mixed-type compound questions (subparts have different answer types) | **138 / 644 questions (21%)** | Part b shows a numeric text input where it should show MCQ option list |
| Subparts whose answer type ≠ parent Question.question_type | **272 / 1734 subparts** | Wrong input widget; multi_select renders as fill-in-the-blank |
| Subparts whose question_text is wrapped HTML (`<div>`, `<p>`, `<sub>`, `<sup>`) | **481 / 1734** | Tags either render as literal text, or strip formatting depending on path |
| `\begin{array}…\end{array}` LaTeX environments stored without `$…$` wrapping | many | Renders as raw `\begin{array}{c|lcr} Salary & \text{1000-3000}…` |
| Subparts with attached image | only **137 / 1734** | Most figure-bearing questions still missing diagrams |
| Cabinet `cabinet:<id>` tag collisions (same ID across chapters) | **33 / 679 source questions** never updated on re-import | Some questions reimported under wrong taxonomy / not at all |
| Subparts with table structures in solution | 6 | Solution renders raw `\begin{array}` |
| Hint text gated correctly? | unknown | Audit pending |

---

## B. Why this matters

The Cabinet bank is the *entire* real K–12 content of the platform — 679
real questions, K–12 mathematics + science, in production-equivalent form.
Until every gap above is closed:

- Real teachers can't assign real questions without manually rewriting them.
- The V2 brand polish (M1–M3) doesn't matter on the page that students
  actually see.
- AI features that train on or recommend this content (M7 weekly reports,
  parent insights, hint system) reference broken text in their outputs.

This is the single highest-leverage initiative on the board.

---

## C. Breakdown — six sub-initiatives, each PR-sized

### M7-03 — Per-subpart question type (schema)

**Problem**: Cabinet's `type` field is **per subpart** (1=mcq, 2=multi_select, 3=numeric, 4=fill_blank). Modern stores `question_type` only on `Question`. The importer picks the first subpart's type for the whole question. 138 questions (21%) have heterogeneous subparts that consequently render wrong.

**Fix**:
- New migration: add `QuestionSubpart.subpart_type` (TextChoices, same set as `QuestionType`). Backfill from `correct_answer["type"]` for existing rows.
- Update importer to set `subpart_type` per subpart.
- Question-level `question_type` becomes a *summary* — set to `"compound"` when subparts are heterogeneous, else the unanimous subpart type.
- Update `QuestionSubpartStudentSerializer` to expose `subpart_type`.
- Frontend: `SubpartInput.tsx` switches on `subpart.subpart_type` instead of `question.question_type` for the input widget.
- Update grader: dispatch per subpart, not per question.

**Tests**: re-import 1734 subparts, assert every `subpart_type` is non-null; assert compound questions are flagged; frontend snapshot for a compound question shows MCQ widget for one subpart and numeric input for another.

### M7-04 — `RichContent` renderer (block math + LaTeX environments)

**Problem**: The M7-01 design plan was filed (`2026-05-30-plan.md`) but the actual `RichContent` primitive only exists on an unmerged local branch (`feat/2026-05-30-question-rich-content`). The current `QuestionCard.renderMixedContent` handles only `$…$` and `$$…$$` — no `\(…\)`, no `\[…\]`, no HTML sanitisation, no `\begin{array}…\end{array}` environment detection.

**Fix**:
- Land M7-01 as planned: `shared/ui/RichContent.tsx` with DOMPurify + KaTeX, wired into `QuestionCard`, SRS drill, teacher Question Bank, teacher CreateQuestionPage preview.
- **Plus an addition to that plan**: also detect un-delimited LaTeX environments (`\begin{X}…\end{X}` for `array`, `tabular`, `matrix`, `align`, `equation`, `cases`, etc.) and treat them as block math.
- Sanitise allowlist includes `table, thead, tbody, tr, td, th` for HTML-table questions.

**Tests**: snapshot tests over the actual broken examples from the 2026-05-30 audit:
- Q with `<div>` + inline `\(…\)` — renders without literal tags
- Q with bare `\begin{array}{c|lcr}…\end{array}` — typesets as math
- Q with table + KaTeX — both render

### M7-05 — Tag-collision fix on re-import

**Problem**: Cabinet question IDs (e.g. `1`, `2`, `3`) repeat across chapters. The importer's `cabinet:<id>` tag is global, so 33 questions weren't updated on re-import (they collide and only the first wins).

**Fix**:
- Importer's tag becomes `cabinet:<board>:<school>:<standard>:<subject>:<chapter>:<id>` — guaranteed unique.
- Migration: rewrite existing tag names from `cabinet:<id>` to the full path; lookup the path from the questions' existing chapter/subject FKs.
- Re-run the import; assert all 679 source questions now have unique tags.

### M7-06 — Inline-image extraction

**Problem**: 481 subparts have HTML wrapping; some Cabinet authors embedded `<img src="...">` directly in the HTML rather than relying on a sibling file. The current importer's image-discovery only handles siblings + `img/` subdirectory.

**Fix**:
- Importer scans question_text/solution_text/hint_text for `<img src="...">` references at convert time. If the src is a relative cabinet path, rewrite it to the raw.githubusercontent.com URL. If it's already absolute, leave it.
- DOMPurify allowlist for `<img>` must keep `src` (already does in the M7-04 plan) but restrict to http(s).

**Tests**: corpus scan reports the count of inline images discovered; the rendered HTML preserves them; the renderer is robust to broken / missing image refs.

### M7-07 — Compound question shared stem

**Problem**: Many Cabinet questions had a *shared preamble* (the table, the figure, the scenario) followed by subparts (Part a, Part b, …) each asking different things about that same context. Modern has no question-level "stem" field — so the stem leaks into the first subpart or is missing entirely.

**Fix**:
- New optional field on `Question.stem_text` (TextField, blank=True) — rendered above all subparts.
- Importer: detect when subparts share an identical leading paragraph and lift it into `stem_text`.
- Frontend `QuestionCard` renders `question.stem_text` once above the subpart list.

**Tests**: an importer test on a known compound fixture; a frontend snapshot showing the stem rendered above two subparts.

### M7-08 — `--report-unknowns` triage + cabinet expression coverage

**Problem**: A few cabinet expressions still reference helpers we don't allowlist in `safe_eval_expr`. They fall back gracefully but stay un-substituted in the rendered solution.

**Fix**:
- Add `--report-unknowns` to the importer; scan all token expressions during import; report any name node that's neither a sampled variable, an allowlisted constant, nor an allowlisted function.
- Triage the list; extend `_SAFE_FUNCS` / `_SAFE_CONSTS` accordingly.

**Tests**: assert the report goes from N>0 to 0 (or a stable allowlisted set) on the full cabinet bank.

### M7-09 — Chapter & subject name inference (no mapping required)

**Problem**: The cabinet on-disk layout encodes only legacy MySQL **IDs**
for subject and chapter (e.g. `questions/containers/CBSE/openshiksha/8/12/46/...`).
There is no name in the source data. Without a `--mapping` file, the
importer creates placeholder taxonomy like `Imported Subject 12` and
`Imported Chapter 46` — accurate IDs, useless names. Subjects/chapters
visible to students therefore read as numeric placeholders.

Audit on 2026-05-30 (44 imported subjects/chapters, no mapping file
shipped):

```
$ SELECT COUNT(*) FROM subjects WHERE name LIKE 'Imported Subject %';   -- 4
$ SELECT COUNT(*) FROM chapters WHERE name LIKE 'Imported Chapter %';   -- 51
```

55 placeholder names in the live taxonomy.

**Fix** — inference pipeline that runs once after import:

1. **Content-driven inference (primary signal).** For each placeholder
   chapter, gather (a) the question tags already attached to its
   questions (concept tags like `polynomials`, `linear-equations`,
   `acids-bases` are often present from the cabinet metadata); (b) the
   most-frequent salient noun phrases in `question_text` /
   `solution_text` after stripping LaTeX and stopwords; (c) the
   chapter's standard + subject (already known from the path).
2. **CBSE NCERT cross-reference (corroborating signal).** Ship a
   canonical chapter list per `(standard, subject)` derived from the
   NCERT table-of-contents (e.g. CBSE Class 8 Maths chapters: Rational
   Numbers, Linear Equations in One Variable, Understanding
   Quadrilaterals, …). One small JSON file checked into the repo:
   `backend/openshiksha/apps/core/data/ncert_toc.json`.
3. **LLM disambiguation (last resort, optional).** When (1) + (2) yield
   multiple candidates of similar strength, call the existing Claude
   API integration with a short prompt: `"Standard 8 Maths. Sample
   questions: <three samples>. Which of these NCERT chapter names is
   the best fit? <candidate list>. Reply with the exact chapter name."`
   Inexpensive (≤10 tokens out per chapter) and only fires on the few
   ambiguous chapters that the deterministic pass couldn't pick.

**Where it lives**:
- New management command `infer_taxonomy_names` (separate from the
  importer; importer stays deterministic + idempotent).
- `--dry-run` prints the proposed rename map; `--apply` writes it.
- Re-runnable: skips chapters whose name no longer matches the
  `Imported Chapter %` placeholder pattern, so human-curated renames
  are never overwritten.
- Writes a JSON audit log to
  `backend/openshiksha/apps/core/data/inferred_taxonomy_<date>.json`
  so renames are traceable.

**Tests**:
- Pure unit test for the content-keyword extractor (a fixture chapter
  whose questions are clearly about `polynomials` resolves to
  "Polynomials").
- NCERT cross-reference test: given 8th Maths and `linear-equations`
  keyword, the matching CBSE name "Linear Equations in One Variable"
  is selected.
- End-to-end on the seeded DB: 0 `Imported Chapter %` placeholders
  remaining after `infer_taxonomy_names --apply`.

**Not in scope** for this sub-initiative:
- Translating the chapter name into Hindi (separate i18n work).
- Re-ordering chapters in the curriculum sequence (that's a different
  schema concern — `Chapter.order` already exists and can be set in a
  follow-up).
- Mapping legacy MySQL IDs to a static dictionary; the inference is
  the deliverable.

### M7-11 — Interactive-widget support (sandboxed) — *additive, not in original DoD*

**Problem**: Exactly **one** source question embeds an interactive widget — the
Class 11 Physics Thermodynamics piston/First-Law simulation
(`questions/raw/1/1/11/3/44/22.json`): SVG + inline jQuery `<script>` with a heat
slider (toggles fire/ice) and press-and-hold piston arrows driving a live
`ΔU = ΔQ − ΔW` readout. The M7-04 DOMPurify path correctly strips the `<script>`,
**silently killing the interactivity**. (18 other questions use *static* `<svg>`
diagrams that already survive sanitisation — those need no work.)

**Fix** (full spec in the 2026-06-01 daily plan, items 6a/6b):
- **6a (backend):** importer detects `<script>`/`on*=` handlers, stores the raw
  HTML in a new `QuestionSubpart.interactive_html` behind an `is_interactive`
  flag, and keeps a sanitised, script-free fallback in `question_text`. The raw
  field is **never** rendered into the app DOM directly.
- **6b (frontend):** an `InteractiveWidget` host renders flagged subparts in a
  sandboxed iframe (`sandbox="allow-scripts"`, **never** `allow-same-origin`) with
  jQuery/jQuery-UI in the srcdoc and image/variable tokens resolved before
  injection.

> **⚠️ Build 6b's sandbox host for reuse, not as a throwaway.** It is the **seed**
> for the [Interactive Widgets Framework](interactive-widgets-framework.md)
> initiative (IW-1 hardens this exact host into the reusable widget runtime;
> the thermo sim becomes the framework's first registry widget in IW-2). Keep the
> host/iframe boundary and the host↔widget message shape clean and generic so it
> can graduate into `@os/widget-sdk` later instead of being rewritten.

**Scope note**: M7-11 is **additive** — it introduces a new content class that was
not part of this initiative's original Definition of Done. If it slips it does
**not** block declaring Cabinet Data Fidelity complete (the items below close on
the original 644-question content). Track it as the immediate follow-on.

---

## D. Cross-cutting Definition of Done

- All 644 imported questions render with the correct input widgets per subpart.
- No raw HTML tags or `\begin{}` syntax visible to students.
- Every available cabinet image is attached (target: ≥500 of the 700+ on disk).
- Every cabinet question_id maps to exactly one modern Question.
- **Zero `Imported Subject %` / `Imported Chapter %` placeholders in the
  live taxonomy** — every chapter has a recognisable CBSE name.
- M7-02's substitution metric stays at 0 leaks; no regression on the 620
  backend test suite.
- One change doc per sub-initiative, link from this file.
- This document moves to "✅ Complete" at the bottom of the V2 initiative ledger.

---

## E. Sequencing

| Order | Sub-initiative | Why this order |
|---:|---|---|
| 1 | **M7-04** — `RichContent` renderer + `\begin{X}` env support | Largest visual impact; unblocks every other diagnosis (you can actually *see* the broken cases) |
| 2 | **M7-03** — Per-subpart question type | Highest correctness impact; 21% of compound questions are broken |
| 3 | **M7-05** — Tag-collision fix + re-import | Recovers 33 lost questions; idempotency for all future imports |
| 4 | **M7-06** — Inline-image extraction | Pure quality lift; no model change |
| 5 | **M7-07** — Shared stem | Cosmetic but visible; small migration |
| 6 | **M7-08** — Expression coverage triage | Long tail; do last when the metric is observable |
| 7 | **M7-09** — Chapter & subject name inference (NCERT + content) | Cosmetic but pervasive; replaces 55 placeholder names visible to teachers, students, parents |

Each is one PR. Land in order; the next session's daily plan picks the
top-most unfinished sub-initiative.

---

## F. Out of scope (deferred until this initiative closes)

- M7-10 Filter/search/sort on Browse, Question Bank, assignment lists.
- M4-01 Student Dashboard in V2 language.
- M1-06 Rest of the V2 primitives (`Input`, severity `Badge`, `Stat`, `SectionHeading`, `EmptyState`).
- Teacher AI Assistant (auto-assignment, open-ended grading).

These are good work but they polish a surface whose underlying content is
still broken. Returning to them after the Cabinet bank renders correctly
keeps the platform focused on real classroom value.
