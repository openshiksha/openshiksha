# Fix assignment-publish 500: migrate on container start + readable dev logs

**Date:** 2026-06-11
**Classification:** Fix (infra + dev ergonomics)

## Summary

Publishing an assignment against the Docker stack failed with a 500. The
backend log was a wall of `django.template VariableDoesNotExist` tracebacks
(`Failed lookup for key [name] in <URLResolver …>`), which is **not** the
bug — it's Django's own technical 404/500 debug pages probing optional
template variables, logged because dev settings run the `django` logger at
DEBUG. Buried beneath the noise was the real exception:

```
django.db.utils.ProgrammingError: relation "problem_set_versions" does not exist
```

The dockerized Postgres had never been migrated for AIV-7's
`ProblemSetVersion` table (migrations 0025/0026), so the version-pinning
query in `AssignmentSerializer.create` exploded. The compose backend service
ran bare `runserver` — nothing ever applied migrations, so the container DB
silently drifts every time new migrations land.

## What changed

- **`docker-compose.yml`** — backend command is now
  `sh -c "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"`,
  so the schema always matches the code on container start.
- **`backend/openshiksha/settings/development.py`** — `django.template`
  logger pinned to INFO (console only, no propagate). The DEBUG-level
  VariableDoesNotExist flood from Django's internal debug pages buried the
  actual error several screens up; real template errors still surface (they
  raise, they don't log-and-continue).

No application code change — `AssignmentSerializer.create` was correct; the
schema was missing.

## Verification

- Live DB migrated (incl. previously missed `django_celery_results`
  migrations applied on the new container boot).
- End-to-end smoke test inside the container: teacher POST
  `/api/v1/assignments/` → **201**, `problem_set_version` pinned — twice
  (before and after recreating the container with the new command).
- `manage.py check` clean; `docker compose config` valid.
