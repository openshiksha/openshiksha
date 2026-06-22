# `legacy/` — the retired OpenShiksha monolith (archived)

This directory holds the **original OpenShiksha application** — a Python 2.7 /
Django 1.11 monolith — kept here **for historical reference only**. It is **not
built, tested, deployed, or maintained**, and nothing in the modern stack imports
from it.

It was moved here (out of the repository root) on 2026-06-21 as part of the
open-source readiness cleanup, so the root reads as the current stack. Git history
for these files is preserved across the move.

## What replaced it

The live application is the **modern stack** at the repository root:

| Concern  | Legacy (here)                     | Modern (repo root)            |
| -------- | --------------------------------- | ----------------------------- |
| Backend  | Django 1.11 / Python 2.7 monolith | `backend/` — Django 6, Python 3.12, DRF, Daphne/ASGI |
| Frontend | server-rendered Django templates  | `frontend_modern/` — React 18 + Vite |
| Deploy   | `devops/` (nginx + gunicorn)      | `k8s/` (kustomize → k3s)      |
| Content  | `cabinet/` + the Cabinet service  | imported into the DB (`backend/.../import_cabinet_questions`) |

The legacy Django apps (`core`, `cabinet`, `edge`, `lodge`, `focus`, `grader`,
`ink`, `pylon`, `croupier`, `challenge`, `concierge`, `sphinx`, `frontend`, …)
each have a modern successor under `backend/openshiksha/apps/`.

## Running it (only if you really need to)

It targets an EOL runtime (Python 2.7) and EOL Debian base images whose package
repos were archived in 2024, so it will not build out of the box. If you must
inspect its behaviour, do so from **inside this directory** (it is self-contained:
`manage.py`, `openshiksha/settings.py`, and the apps all sit here). Treat it as
read-only history.
