# 2026-06-22 — OSS-9: README product screenshots

**Summary.** Add a `## Screenshots` section to the README (right after
`## What it is`) showing the current V2 product, plus a demo-login note so a
reader can reach those screens themselves.

**Classification.** Improve.

**Initiative.** Open-Source Readiness (Priority 1) — backlog item OSS-9.

## What changed

- Copied three current-product shots from the churning initiative-internal
  `docs/initiatives/screenshots/` into a stable public `docs/screenshots/`:
  `landing.jpg` (from `home.jpg`), `student-dashboard.png`,
  `teacher-question-bank.png` (from `v2-question-bank.png`).
- README: new `## Screenshots` section — a three-column table of clickable
  thumbnails (landing / student dashboard / teacher question bank) placed
  before the architecture deep-dive so the product is visible first.
- Added a demo-login note pointing at `seed_demo_data` and the demo accounts
  (`student_demo` / `teacher_demo` / `parent_demo` / `admin_demo`, password
  `demo1234` — sourced from `seed_demo_data.py`).

## Why this is an improvement

A picture closes the "what is this?" gap faster than prose. The shots are
already-captured, already-reviewed V2 (orange/Fraunces) screens, so no fresh
capture pass was needed. They live under a stable `docs/screenshots/` path so
the public README never deep-links the churning initiative-internal folder.

## Tests

- README renders the embedded images (GitHub relative paths resolve from repo
  root); each image is < 200 KB.
- `pre-commit` green. Docs-only — no code paths, no CI regression risk.

## Next steps

OSS-8 (Mermaid architecture diagram) next — also touches the README, sequenced
after this so it rebases cleanly.
