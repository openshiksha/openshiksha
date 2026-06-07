# OpenShiksha — k3s deploy

This is how the **modern** OpenShiksha stack (Django 4.2 backend +
React/Vite frontend + Celery + Postgres + Redis) gets to qa and prod on the
`k3s-personal-server` cluster.

> **The legacy root `Dockerfile` (Python 2.7 / Django 1.11 / nginx-in-image)
> is no longer built or deployed.** CI used to publish it; merging
> `modernization` → `qa` would fail because the Debian Buster repos it
> depends on were archived in mid-2024. The legacy file is still in the repo
> for reference but is excluded from the pipeline.

## What's running

Per-environment namespace:

| Env  | Namespace          | Ingress host         |
| ---- | ------------------ | -------------------- |
| qa   | `openshiksha-qa`   | `qa.openshiksha.org` |
| prod | `openshiksha-prod` | `openshiksha.org`    |

Each namespace contains:

- `Deployment/backend` — Django 4.2 served by Daphne (ASGI).
- `Deployment/frontend` — React SPA built with Vite, served by nginx.
- `Deployment/celery-worker` — same backend image, `celery worker` CMD.
- `Deployment/celery-beat` — same backend image, `celery beat` CMD (strictly
  1 replica, `strategy: Recreate` — multiple beats would double-fire every
  scheduled task).
- `StatefulSet/postgres` — Postgres 15 on a 10 Gi PVC.
- `StatefulSet/redis` — Redis 7 with AOF persistence on a 2 Gi PVC.
- `Ingress/openshiksha` — Traefik (k3s default). `/api/*`, `/admin/*`,
  `/static/*` → backend; everything else → frontend.
- `ConfigMap/openshiksha-config` — non-secret env.
- `Secret/openshiksha-secrets` — secret env (NOT in git, see below).

Manifests are kustomize:

```
k8s/
  base/                # the shape — neutral on namespace/host/tag
  overlays/qa/         # namespace=openshiksha-qa, host=qa.openshiksha.org
  overlays/prod/       # namespace=openshiksha-prod, host=openshiksha.org
                       # + 2 replicas for backend/frontend
```

## How a deploy actually happens

1. PR merged into `qa` (or `prod`).
2. CI runs the existing lint/typecheck/test/frontend jobs.
3. `build-publish` (matrix: backend + frontend) builds the two prod
   Dockerfiles, pushes to `ghcr.io/openshiksha/openshiksha-{backend,frontend}`
   with two tags each: the branch name (`qa` / `prod`) and the commit SHA.
4. `deploy-qa` / `deploy-prod` —
   - Pulls the cluster kubeconfig from `secrets.KUBECONFIG`.
   - `kustomize edit set image …:<sha>` so the Deployment spec is pinned to
     the digest just built (re-pushing a `:qa` tag doesn't trigger a rollout
     by itself; pinning by SHA does).
   - `kubectl apply -k k8s/overlays/{qa,prod}`.
   - `kubectl rollout status` on every Deployment / StatefulSet with timeouts.

The legacy `kubectl rollout restart deployment openshiksha openshiksha-celery-worker openshiksha-celery-beat -n openshiksha`
step is **gone**. Those deployments still sit in the old `openshiksha`
namespace until someone runs `kubectl delete ns openshiksha`.

## One-time bootstrap (per environment)

Three things have to be true on the first deploy of an environment, or CI
will look like it succeeded but nothing will actually go out:

1. **The GitHub Environment exists.** The deploy jobs declare
   `environment: qa` / `environment: prod`. If those environments don't
   exist in the repo's Settings → Environments page, the jobs **silently
   skip** — no error, no deploy. Create both (no approvers needed unless you
   want them). One-time per repo.
2. **DNS points at the cluster.** Add an A/CNAME for the env's hostname
   (`qa.openshiksha.org`, `openshiksha.org`) pointing at the k3s node's
   external IP. Traefik picks up the Ingress as soon as the manifest is
   applied, but nothing can reach it without DNS.
3. **The Secret exists in the namespace** (covered in detail below). Without
   this, `kubectl apply` of the manifests succeeds and creates the
   namespace, but the backend / celery pods crash-loop and the CI
   `rollout status` step times out.

The `Secret` is not committed to git. Before the first deploy, populate it
out-of-band:

```bash
# Replace REPLACE-ME values. Random 50-char strings are fine for SECRET_KEY
# and JWT_SECRET_KEY. The Postgres password becomes part of DATABASE_URL.
PG_PASSWORD="$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-32)"

kubectl create namespace openshiksha-qa --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic openshiksha-secrets -n openshiksha-qa \
  --from-literal=SECRET_KEY="$(openssl rand -base64 50)" \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 50)" \
  --from-literal=POSTGRES_PASSWORD="$PG_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql://openshiksha:${PG_PASSWORD}@postgres:5432/openshiksha" \
  --from-literal=REDIS_URL="redis://redis:6379/0" \
  --from-literal=CELERY_BROKER_URL="redis://redis:6379/1" \
  --from-literal=CELERY_RESULT_BACKEND="redis://redis:6379/2" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-…" \
  --from-literal=EMAIL_HOST_USER="" \
  --from-literal=EMAIL_HOST_PASSWORD=""
```

Repeat for `openshiksha-prod` with a fresh Postgres password.

### TLS

The Ingress is shipped **without TLS** so the first deploy works on a cluster
that hasn't got cert-manager yet. To enable:

1. Install cert-manager + a `ClusterIssuer` named `letsencrypt-prod`
   (standard ACME-HTTP01 with Traefik).
2. Uncomment the `cert-manager.io/cluster-issuer` annotation and the `tls:`
   block in [`k8s/base/ingress.yaml`](../../k8s/base/ingress.yaml).

Backend prod settings already include `SECURE_PROXY_SSL_HEADER =
('HTTP_X_FORWARDED_PROTO', 'https')` so it respects the Traefik-terminated
TLS once it's on; without that, `SECURE_SSL_REDIRECT` would redirect-loop.

## Local sanity-checks for these manifests

You don't need a cluster to validate the YAML:

```bash
# Render the overlay and pipe through `kubectl apply --dry-run=client` to
# catch typos / bad refs / mismatched names. No cluster needed.
kubectl kustomize k8s/overlays/qa   | kubectl apply --dry-run=client -f -
kubectl kustomize k8s/overlays/prod | kubectl apply --dry-run=client -f -
```

To build the production images locally:

```bash
docker build -f backend/Dockerfile.prod         -t openshiksha-backend:dev  backend
docker build -f frontend_modern/Dockerfile.prod -t openshiksha-frontend:dev frontend_modern
```

## Rollback

```bash
kubectl -n openshiksha-qa rollout undo deployment/backend
kubectl -n openshiksha-qa rollout undo deployment/frontend
```

Or — cleaner if a bad image is already pulled by other Deployments — re-set
the image to a known-good SHA and re-apply:

```bash
cd k8s/overlays/qa
kustomize edit set image \
  ghcr.io/openshiksha/openshiksha-backend=ghcr.io/openshiksha/openshiksha-backend:<good-sha> \
  ghcr.io/openshiksha/openshiksha-frontend=ghcr.io/openshiksha/openshiksha-frontend:<good-sha>
kubectl apply -k .
```

## What to delete from the cluster (one-time cleanup)

When you're confident nothing's pointing at the legacy stack:

```bash
kubectl delete ns openshiksha
```

(The new modern stack lives in `openshiksha-qa` / `openshiksha-prod` — this
deletion only nukes the legacy Django 1.11 monolith.)
