# 2026-06-22 — OSS-8: renderable architecture diagram

**Summary.** Replace the ASCII-art architecture block in the README with a
GitHub-rendered **Mermaid** `flowchart`, keeping the stack table and preserving
the ASCII as a collapsed `<details>` fallback.

**Classification.** Improve.

**Initiative.** Open-Source Readiness (Priority 1) — backlog item OSS-8.

## What changed

- README `## Architecture`: the fenced ASCII block is now a ` ```mermaid `
  `flowchart TD` modelling the real request flow:
  - `Browser --HTTPS--> Traefik (k3s ingress)`
  - Traefik routes `/api/* /admin/* /static/*` → **Django + Daphne backend**,
    everything else → **React SPA (nginx)**
  - backend → **PostgreSQL** (data) + **Redis** (cache/broker)
  - **Celery worker + beat** ← Redis (async grading, AI tasks)
  - backend → **AI providers** (Gemini / Claude, Ollama fallback)
- The existing stack table is **retained** (diagram = topology, table = tech).
- The original ASCII art is kept inside a collapsed `<details>` block as a
  fallback for non-Mermaid renderers.

## Why this is an improvement

GitHub renders ` ```mermaid ` natively, so the architecture now communicates at
a glance instead of as monospace art, and is far easier to extend. Same truth,
more legible. Node labels are kept short so it renders on mobile GitHub.

## Tests

- Mermaid block validated for parse correctness (flowchart node/edge syntax,
  quoted labels, `<br/>` line breaks, cylinder/hexagon shapes).
- Topology matches the prose in `## CI/CD pipeline` and `docs/deploy/README.md`.
- `pre-commit` green. Docs-only — no CI regression risk.

## Next steps

OSS-7 (consolidate root dev docs under `docs/dev/`) — last README-touching item.
