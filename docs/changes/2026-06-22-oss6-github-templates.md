# 2026-06-22 — OSS-6: GitHub issue & PR templates

**Summary.** Add community contribution scaffolding to `.github/`: two issue
templates (bug report, feature request), an issue-chooser config that routes
security reports privately, and a pull-request template mirroring the repo's
real conventions.

**Classification.** New.

**Initiative.** Open-Source Readiness (Priority 1) — backlog item OSS-6.

## Legacy reference

None — the archived Django 1.11 monolith was a private internal repo with no
community scaffolding. Net-new repository capability.

## What changed

- `.github/ISSUE_TEMPLATE/bug_report.md` — front-matter (`labels: bug`,
  `title: "[Bug]: "`); sections for what happened / expected / repro steps /
  environment (browser + role) / screenshots / severity.
- `.github/ISSUE_TEMPLATE/feature_request.md` — (`labels: enhancement`,
  `title: "[Feature]: "`); problem / proposed solution / who benefits (role) /
  alternatives.
- `.github/ISSUE_TEMPLATE/config.yml` — `blank_issues_enabled: false` with a
  `contact_links` entry routing vulnerabilities to the security policy
  (SECURITY.md) instead of public issues.
- `.github/pull_request_template.md` — summary / type (port/improve/new/fix/docs) /
  initiative+increment / how tested / checklist (targets `modernization`, CI green,
  migration drift, no secrets, commit conventions).

## Tests

- YAML front-matter of each template validated with `yaml.safe_load`.
- Chooser rendering is GitHub-side (cannot be tested locally).
- Docs-only — no backend/frontend code touched, no CI regression risk.

## Next steps

OSS-9 (README screenshots) next in the batch.
