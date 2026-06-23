# 2026-06-22 — OSS-10: repo metadata + license verification

**Summary.** Set the GitHub repo's description, homepage, and topics; verify the
license is auto-detected; badge it in the README. Closes the Open-Source
Readiness initiative (DoD met).

**Classification.** New + Verify.

**Initiative.** Open-Source Readiness (Priority 1) — backlog item OSS-10 (final).

## What changed

- **Repo metadata** (via `gh repo edit`, admin scope was present — no manual
  follow-up needed):
  - description: *"Modern K-12 practice-learning platform for India — Django +
    React, AI-assisted."*
  - homepage: `https://openshiksha.org`
  - topics: `education, edtech, k12, django, react, typescript, india,
    learning-platform` (added alongside the pre-existing `hacktoberfest`).
- **License verification.** `gh repo view --json licenseInfo` already reports
  `mpl-2.0` (Mozilla Public License 2.0) — GitHub's licensee detector recognises
  the existing `LICENSE.md`, so no plain-`LICENSE` copy was needed.
- **README:**
  - License badge upgraded from the generic "see LICENSE" to a proper
    `MPL 2.0` shields.io badge.
  - `## License` section now names MPL-2.0 explicitly and links `LICENSE.md`.
- **Ledger / STATUS.** Marked OSS-6..10 shipped and the initiative **Done — DoD
  met**; recorded that Accessibility (Priority 2) becomes the top active
  initiative.

## Tests

- `gh repo view openshiksha/openshiksha --json description,homepageUrl,repositoryTopics`
  confirms the new metadata.
- `gh repo view --json licenseInfo` → `mpl-2.0` (sidebar will show the detected
  license).
- README badges render (shields.io). `pre-commit` green. Docs/metadata-only —
  no CI regression risk.

## Next steps

Open-Source Readiness is complete. The board promotes **Accessibility — WCAG 2.1
AA** (Batch 2 already planned in `docs/daily-plans/2026-06-20-plan.md`).
