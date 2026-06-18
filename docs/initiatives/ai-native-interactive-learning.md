# AI-Native Interactive Learning

> ## 🔒 Routine ownership — read this first
> This initiative is built **exclusively** by the `openshiksha-ai-features`
> scheduled routine. The `openshiksha-plan`, `openshiksha-execute`, and
> `openshiksha-dependabot` routines **MUST NOT** plan, select, or build any of
> its increments — even when it is the only thing with open work. It is
> intentionally **excluded from the priority table** in
> [`STATUS.md`](STATUS.md). The ai-features routine, in turn, works **only**
> from this backlog — not the general roadmap.

**Status:** 🟢 Active (promoted 2026-06-15) · **Owner:** `openshiksha-ai-features` routine

---

## North Star

Build, one iron-clad increment at a time, toward a **~2-minute "golden-path"
demo** of OpenShiksha where **every beat is (a) not in the market, (b) tactile
and verifiable on screen, and (c) iron-clad by construction.** The routine
literally *assembles the demo* over time (see [`docs/demo/golden-path.md`](../demo/golden-path.md)).

**Flagship capability (Phase 1):** *AI builds a working, auto-graded interactive
widget from a plain-English description.* A teacher types "a number line where
students mark ¾" and a validated, sandboxed, gradeable widget appears in the
live preview. Most ed-tech AI is a chatbot or a text question generator — AI
that emits a **validated interactive manipulative** is the differentiated,
"not-in-the-market" moment, and it's the *safest* AI pattern: the output is
schema-validated data, never code.

## Why this exists

OpenShiksha is pre-launch with no real usage, and its feature set is at parity.
The next value isn't more polish or more dashboards (those read as "air" — clever
but unfalsifiable). It's a small number of capabilities a viewer can watch *work
and be correct*. This initiative builds exactly those, on top of the two things
the platform already does well: **deterministic, sandboxed interactivity** (the
Interactive Widgets Framework) and a **bounded LLM layer** (the explanation/
hint/grading cascade).

## Principles — the iron-clad bar (every increment ships meeting all of these)

1. **AI lives on the backend/host, never in the sandbox.** The widget runtime
   stays deterministic and network-less by design; the host mediates any AI call.
2. **AI is never in the grading/correctness path.** Grades come from the existing
   per-subpart grader (or a deterministic check). AI only **authors** or **coaches**.
3. **Every AI output that becomes data is schema-validated before it reaches the
   runtime or DB** — invalid output is repaired or rejected, never rendered raw.
4. **Always a deterministic fallback.** No key / timeout / malformed output still
   yields a working result (a safe default config, a static hint), proven by a test.
5. **Grounded, not free-floating.** AI sees the real state (the kind's schema, the
   actual numbers, the student's reported value) so it can't hallucinate about
   what it can't see.
6. **Honest provenance.** Real LLM output wears the `✨ AI-generated` `AIBadge`;
   deterministic/stub output wears the neutral `Auto-…` badge. Stub is never
   shown as if it were a real generation.
7. **Demo-able + tested, in the same increment.** Each increment extends the
   golden-path script and ships a test that exercises the **real path and the
   fallback path** — never as a follow-up.

## Foundation — what already exists (reuse, don't reinvent)

- **Widgets framework** (`frontend_modern/src/widgets/`, [initiative](interactive-widgets-framework.md)):
  sandboxed `allow-scripts` iframe; registry kinds `thermo-piston`,
  `number-line`, `function-plotter`, `fraction-bar` (+ admin `custom-html`,
  built-in `studio-scene`); each kind has a `params.schema.json`;
  answer-producing widgets report through the protocol into the **per-subpart
  grader**; `WidgetGalleryPanel` (IW-5) already renders a **live sandbox
  preview** + a schema-driven config form inside `CreateQuestionPage`; croupier
  `{{var}}` substitution flows into `widget_config` per student.
- **Backend widget guard** (`apps/core/widgets.py`): `KNOWN_WIDGET_KINDS` +
  `validate_widget_config`. ⚠️ Today it enforces only the **floor** (kind must be
  known, config must be a dict) — **per-kind JSON-Schema validation is NOT yet
  server-side.** DTB-1 closes that, because the whole initiative's safety rests
  on it.
- **LLM layer** (`apps/ai/llm_client.py`): Claude → Gemini → Ollama → **stub**
  cascade, `model_used` on serializers, `resolve_ai_language` (en/hi). Endpoints
  use the `@action generate` + 202-poll async pattern; provenance via the shared
  `AIBadge`.

## Backlog — Phase 1: Describe-to-Build (PR-sized, lowest-risk-first)

| ID | Increment | Status |
|----|-----------|--------|
| DTB-1 | **Server-side per-kind schema validation** (the guardrail keystone). Bring each kind's JSON Schema to a canonical backend source; `validate_widget_config` enforces the kind's schema, not just the floor. Reject invalid configs with a clear 400. **No AI yet.** Tests: a valid + an invalid config per kind. | ✅ Done (#365) |
| DTB-2 | **`/ai/widget-authoring/` endpoint**: NL prompt + the known kinds/schemas → proposes `{widget_kind, widget_config}`, **always validated by DTB-1**; on invalid → bounded repair (clamp / one re-ask) → deterministic **stub default** for the best-guess kind. Returns `model_used`. Tests: real-mocked **and** stub both return a **schema-valid** config; malformed LLM output never escapes. | ✅ Done (#372) |
| DTB-3 | **"Describe a widget" UI** in `WidgetGalleryPanel` / `CreateQuestionPage`: a prompt box → calls the endpoint → renders the proposal in the **existing live sandbox preview** → teacher edits via the existing schema form → attach. `AIBadge`, loading/empty/error states, friendly fallback line. The on-screen wow. | ⬜ Next |
| DTB-4 | **Demo golden-path beat + capture**: create/extend `docs/demo/golden-path.md` with the describe-it beat; capture a screenshot/gif; an e2e smoke that drives type → generate → render → (student) grade. First use of the "routine accumulates the demo" mechanic. | ⬜ |
| DTB-5 | **Variable-aware generation**: AI may emit `{{var}}` bindings so a generated widget is **per-student randomized** via croupier ("a number line marking a random fraction" differs per student). Deepens the wow; reuses the existing substitution path. | ⬜ |

**Phase 1 DoD:** a teacher types a description → a schema-valid, sandboxed,
auto-graded widget renders and attaches — provably, with the stub path tested —
and the describe-it beat records cleanly into the golden path.

## Later phases (deliberate, not started — the routine advances them only after Phase 1)

- **Phase 2 — Guided step-validator.** Student solves an equation step by step; a
  deterministic engine (extend the `function-plotter` parser / `safe_eval_expr`)
  checks each line's algebraic equivalence; AI **only** explains a wrong step.
  Correctness deterministic; AI coaches. The trustworthy-math beat.
- **Phase 3 — Propose-and-verify practice bank.** AI authors widget problems; the
  deterministic engine confirms a **unique correct answer** before any ship;
  feeds SRS / difficulty calibration. AI proposes, the engine disposes.

## Out of scope (the "air" anti-patterns)

- **Free-form AI tutor chat.** Unbounded, ungradeable, hallucination-prone — the
  opposite of iron-clad. (There is a diverged `ai/2026-06-04-ai-tutor-chat`
  branch in the STATUS backlog; this initiative is **not** that.)
- **Arbitrary teacher code execution.** AI emits *config interpreted as data*,
  validated against a schema — never code, never `eval`/`Function`/`<script>`.
- **AI anywhere in the grading path.** Always deterministic correctness.

## Definition of Done (per increment)

- Meets the 7-point iron-clad bar above (validated · deterministic fallback +
  its test · grounded · honest `AIBadge` · demo beat · AI-out-of-grading).
- Build/lint/types/tests green (`pytest` if backend; `npm run lint && npx tsc
  --noEmit && npx vitest run` if frontend); new UI has a Vitest file.
- Ledger row appended below; the golden-path doc extended when a beat lands.

## Progress Ledger

| Date | Increment | PR | Learning |
|------|-----------|----|----------|
| 2026-06-15 | Initiative promoted; Phase 1 (DTB-1..5) scoped. Owned exclusively by the ai-features routine. | _(this doc)_ | Grounded: `validate_widget_config` is floor-only today — DTB-1 (server-side per-kind schema validation) is the safety keystone the AI authoring rides on. |
| 2026-06-15 | **DTB-1 shipped** — server-side per-kind schema validation. Each kind's `params.schema.json` is **vendored** into `apps/core/data/widget_schemas/` (deploy-robust, parity-guarded against the frontend source); `validate_widget_config` now enforces the full Draft-2020-12 schema (types/bounds/enums/`required`/`additionalProperties`), rejecting bad configs with a clear 400. Guardrail keystone for DTB-2+. Golden-path Beat 0 + 16 tests (valid + invalid per kind, `{{var}}` tolerance, missing-schema floor fallback, parity). | #365 | jsonschema's bounds keywords already skip non-number instances, so a pure `{{var}}` token only trips `type`/`enum` — filtering those by `err.instance` gives clean croupier tolerance via **composition**, avoiding the deprecated validator subclassing. Vendoring (not cross-tree path reads) keeps validation working where the frontend tree is absent. |
| 2026-06-17 | **DTB-2 shipped** — `POST /ai/widget-authoring/` (teacher-only). NL description + the four authorable kinds' vendored schemas → LLM proposes `{widget_kind, widget_config}` via the existing Claude tool-use / Gemini-Ollama-JSON cascade. Every proposal runs the DTB-1 guardrail: **validate → deterministic clamp-repair (drop unknown keys, clamp bounds, fix enums) → safe default**, so the returned config is *always* schema-valid. Honest provenance: `ai_available`/`model_used`; the canned default reports `ai_available:false`. New widget-domain helpers in `apps/core/widgets.py` (`AI_AUTHORABLE_WIDGET_KINDS`, `SAFE_DEFAULT_CONFIGS`, `repair_widget_config`, `is_valid_widget_config`). Golden-path Beat 1 + 12 tests (real, clamp-repair, un-salvageable, no-provider — each asserted schema-valid; endpoint permission/shape). | #372 | Keeping the deterministic guardrail (defaults + clamp-repair + bool validation) in `widgets.py` and letting `llm_client` only orchestrate the LLM gives a clean seam: the repair/fallback logic is pure and unit-testable without any LLM mock, and `generate_widget_config` reuses the shared `_call_anthropic_tool` so there's no parallel provider path. Provenance honesty needs a distinction the question generator lacks — a *clamped* config is still AI (`ai_available:true, repaired:true`), but a *discarded* one that falls to the canned default is `Auto-…` (`ai_available:false`). |
