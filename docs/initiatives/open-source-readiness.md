# Open-Source Readiness

## North Star

A newcomer lands on `github.com/openshiksha/openshiksha`, and within **five
minutes** understands *what it is*, *how it's built*, *how to run it locally*, and
*how it ships to production* — and can make their first contribution without
asking anyone. The repository root reads as **one coherent modern stack**, the
README tells the whole story, and the standard open-source scaffolding (license,
contributing guide, security policy, templates) is present and accurate.

This initiative makes OpenShiksha a repository we'd be proud to point the public at.

## Why now

The platform is **live in production** (modern stack on k3s, `openshiksha.org`,
full CI/CD). The code is ready; the *repository* isn't:

- The root was cluttered with the **retired Django 1.11 monolith** (~660 files)
  sitting next to the modern stack, so the structure didn't communicate the
  current architecture.
- The root **README was 13 lines** — no architecture, no quickstart, no mention
  of the CI/CD pipeline that actually governs the project.
- Standard OSS files (CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, issue/PR
  templates) were absent, and dev docs were scattered as loose root `.md` files.

Releasing as open source is the trigger: first impressions and contributor
on-ramp now matter.

## Principles

- **The root is the modern stack.** Anything retired lives under `legacy/`,
  clearly labelled, never built.
- **Document what's true, not aspirational.** The README describes the real
  CI/CD pipeline, the real branch→env mapping, the real deploy path.
- **One reviewable PR per increment**, same cadence the repo ships daily. Big
  mechanical moves (file relocations) stay separate from prose changes.
- **No secrets, ever.** Treat every increment as a chance to confirm nothing
  sensitive is tracked.
- **Lower the contribution bar each pass** — a missing template, an unclear
  setup step, a stale link is a contributor lost.

## Definition of Done

- Repo root contains only the modern stack + shared config + docs; the legacy
  monolith is archived under `legacy/` with an explanatory README.
- Root `README.md` covers: what OpenShiksha is, architecture, tech stack, local
  quickstart, the **CI/CD pipeline + branch→env model**, deployment, and links to
  CONTRIBUTING / LICENSE / docs.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` issue +
  PR templates exist and are accurate.
- Dev docs are consolidated/indexed under `docs/` (no stray, stale root guides).
- A clean-checkout contributor can go from `git clone` → running app using only
  the README + linked docs.

## Backlog

### Batch 1 (2026-06-21) — declutter + tell the story
- **OSS-1 — Archive the legacy monolith.** `git mv` the retired Django 1.11 stack
  (`core`, `cabinet`, `edge`, `lodge`, … `manage.py`, `openshiksha/`, `devops/`,
  `scripts/`, `frontend/`, `sphinx/`) into `legacy/` + a `legacy/README.md`;
  delete scratch junk (`test_write.txt`, `write_views.py`); untrack + gitignore
  MCP artifacts and `celerybeat-schedule`. **DoD:** root lists only modern dirs;
  CI still green (nothing modern referenced the moved code).
- **OSS-2 — Rewrite the root README.** What it is → architecture/stack → local
  quickstart (docker-compose) → **CI/CD pipeline + branch→env mapping** → deploy →
  contributing/license/docs links. **DoD:** a newcomer understands and can run it.

### Batch 2 — community scaffolding
- **OSS-3 — `CONTRIBUTING.md`** — branch model, commit/PR conventions, how CI
  gates work, local test commands, the pre-commit hooks.
- **OSS-4 — `SECURITY.md`** — supported versions + private disclosure path.
- **OSS-5 — `CODE_OF_CONDUCT.md`** — adopt Contributor Covenant.
- **OSS-6 — `.github/` templates** — issue templates (bug/feature) + PR template.

### Batch 3 — docs consolidation + polish
- **OSS-7 — Consolidate root dev docs** (`CHEAT_SHEET`, `GIT_STRATEGY`,
  `LOCAL_DEVELOPMENT`, `SETUP_MODERNIZATION`) under `docs/` with an index; fix
  stale links.
- **OSS-8 — Architecture diagram** in the README (request flow: Traefik → backend
  /api,/admin,/static + frontend; Postgres/Redis/Celery).
- **OSS-9 — README screenshots** of the live product (landing + a student/teacher
  surface), with the demo-login note.
- **OSS-10 — Repo metadata** — description, topics, homepage; verify `LICENSE.md`
  is unambiguous and referenced.

## Continuous Improvement

Each pass, do one small hardening task: fix a broken/stale doc link, tighten a
setup step that tripped you, remove a newly-noticed tracked artifact, add a
missing badge, or improve one `.env.example` comment.

## Ledger

| Increment | Status | PR | Date | Learning |
| --- | --- | --- | --- | --- |
| OSS-1 archive legacy monolith | ✅ shipped | (this PR) | 2026-06-21 | ~660 files; all root apps had a modern successor under `backend/`, nothing modern imported them, so the move was inert — CI stayed green. |
| OSS-2 rewrite root README | ✅ shipped | (this PR) | 2026-06-21 | First public-facing doc; documents the real qa→prod-env CI mapping. |
| OSS-3 CONTRIBUTING.md | ✅ shipped | (this PR) | 2026-06-21 | Pulled forward to keep README links clean. |
| OSS-4 SECURITY.md | ✅ shipped | (this PR) | 2026-06-21 | Private disclosure via GitHub advisories + security@openshiksha.org. |
| OSS-5 CODE_OF_CONDUCT.md | ✅ shipped | (this PR) | 2026-06-21 | Contributor Covenant 2.1. |
| OSS-6 `.github/` issue + PR templates | ✅ shipped | [#432](https://github.com/openshiksha/openshiksha/pull/432) | 2026-06-22 | Bug/feature issue templates + PR template; `config.yml` routes vulns to the security policy, not public issues. |
| OSS-9 README product screenshots | ✅ shipped | [#433](https://github.com/openshiksha/openshiksha/pull/433) | 2026-06-22 | 3 V2 shots copied into a stable `docs/screenshots/` (not the churning initiative folder) + a demo-login note (`demo1234`). |
| OSS-8 Mermaid architecture diagram | ✅ shipped | [#434](https://github.com/openshiksha/openshiksha/pull/434) | 2026-06-22 | ASCII → GitHub-rendered Mermaid `flowchart`; ASCII kept as a `<details>` fallback; stack table retained. |
| OSS-7 consolidate root dev docs | ✅ shipped | [#435](https://github.com/openshiksha/openshiksha/pull/435) | 2026-06-22 | `git mv` four guides into `docs/dev/` (kebab-cased, history preserved) + index; repointed all hyperlinks. Remaining grep hits are historical ASCII trees, not links. |
| OSS-10 repo metadata + license badge | ✅ shipped | (this PR) | 2026-06-22 | `gh repo edit` set description/homepage/topics (admin scope present); license already auto-detected as MPL-2.0; README license badge + `## License` updated. |

**Definition of Done met (2026-06-22).** All of OSS-1..10 shipped. A
clean-checkout newcomer can understand, run, and contribute from the README +
linked docs alone: decluttered root, rewritten README with screenshots + a
rendered architecture diagram, consolidated `docs/dev/` index, contributor
templates, and discoverable repo metadata with a detected MPL-2.0 license.

**Open follow-up (not blocking DoD):** the `security@`/`conduct@openshiksha.org`
addresses assume an ImprovMX catch-all is configured — verify or adjust.
