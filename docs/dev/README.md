# Developer guides

Hands-on guides for working in the OpenShiksha repo. Start with the
[README quickstart](../../README.md#quickstart-local), then dive in here.

| Guide | What it covers |
| --- | --- |
| [local-development.md](local-development.md) | Full local setup — Docker Compose (backend + Postgres + Redis + Celery), the Vite dev server, seeding demo data, and the Cabinet question import. |
| [cheat-sheet.md](cheat-sheet.md) | Quick-reference commands for everyday development (running services, tests, migrations, common tasks). |
| [git-strategy.md](git-strategy.md) | The branch model (`feature/* → qa → production`) and the rationale behind it. |
| [setup-modernization.md](setup-modernization.md) | Historical record of how the modern `backend/` + `frontend_modern/` stack was bootstrapped alongside the legacy monolith. |

See also: [Deployment](../deploy/README.md) · [Initiatives](../initiatives/README.md) · [Contributing](../../CONTRIBUTING.md).
