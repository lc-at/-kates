# k8s-aurel

Kubernetes manifests for the Aurel homelab cluster (k3s), including Miniflux, Wallabag, cert-manager, and Sealed Secrets, managed by ArgoCD using an app-of-apps GitOps pattern.

## Repository layout

- `bootstrap/`: cluster bootstrap components (install controllers/operators first).
  - `sealed-secrets/install`: Sealed Secrets controller
  - `cert-manager/install`: cert-manager CRDs and controller
- `base/`: reusable base manifests for workloads and shared config.
- `overlays/prod/`: production composition used for GitOps sync targets.
- `argocd/`: Argo CD application definitions (AppProject and per-component Applications).

## Namespaces

- `cert-manager`: cert-manager, ACME solvers, and Let's Encrypt account secrets.
- `miniflux`: Miniflux RSS reader app and PostgreSQL database.
- `wallabag`: Wallabag bookmark archiver, MariaDB, and Redis cache.

## GitOps deployment (ArgoCD app-of-apps)

The repository uses an **app-of-apps** pattern to manage dependencies and ordering:

### Deployment order (sync waves):

1. **Wave 0:** `bootstrap-sealed-secrets` — Install Sealed Secrets controller
2. **Wave 1:** `bootstrap-cert-manager-install` — Install cert-manager CRDs and controller
3. **Wave 2:** `platform-cert-manager-config` — Configure Let's Encrypt ACME issuer and DNS credentials
4. **Wave 3:** `miniflux` and `wallabag` (parallel) — Deploy applications

### Key features:

- **AppProject scoping:** `homelab` project limits namespace/cluster-resource access (e.g., only cert-manager ClusterIssuer allowed)
- **Pinned revision:** All apps target `main` branch (no floating `HEAD`)
- **Auto-sync enabled:** `prune: true, selfHeal: true` for automatic drift correction
- **Self-describing:** All Argo CD definitions live in `argocd/` for full GitOps coverage

### Deploy with ArgoCD:

```bash
# 1. Create the AppProject and child Applications
kubectl apply -f argocd/project-homelab.yaml

# Then create the root app-of-apps (or create this through Argo UI)
kubectl apply -f argocd/apps/root.yaml

# 2. Monitor sync
kubectl -n argocd get application -w
```

Alternatively, via UI: Connect your repo in Argo CD, create `argocd/apps/root.yaml` Application, and Argo will recursively deploy all child apps in order.

## Manual deployment (without ArgoCD)

If not using ArgoCD, deploy manually in order:

```bash
# 1. Bootstrap controllers
kubectl apply -k bootstrap/sealed-secrets/install
kubectl apply -k bootstrap/cert-manager/install

# 2. Configure cert-manager
kubectl apply -k overlays/prod/cert-manager-config

# 3. Deploy applications
kubectl apply -k overlays/prod/miniflux
kubectl apply -k overlays/prod/wallabag
```

## Validation

Build and inspect manifests before applying:

```bash
# Validate individual overlays
kubectl kustomize bootstrap/sealed-secrets/install
kubectl kustomize bootstrap/cert-manager/install
kubectl kustomize overlays/prod/cert-manager-config
kubectl kustomize overlays/prod/miniflux
kubectl kustomize overlays/prod/wallabag

# Validate all with schema checking (requires kubeconform)
kubeconform -strict -summary <(kubectl kustomize bootstrap)
kubeconform -strict -summary <(kubectl kustomize overlays/prod)
```

## Recovery quick steps

1. Verify controller health:
   - `kubectl -n kube-system get deploy sealed-secrets-controller`
   - `kubectl -n cert-manager get deploy`
2. Verify cert-manager resources:
   - `kubectl get clusterissuer`
   - `kubectl get certificate -A`
3. Verify app rollouts:
   - `kubectl -n miniflux get deploy,pod,svc,ingress`
   - `kubectl -n wallabag get deploy,pod,svc,ingress`

## Architecture notes

- **Sealed Secrets:** All secrets in Git are encrypted with the cluster's sealing key. Only the cluster can decrypt them.
- **cert-manager:** Manages TLS certificates via Let's Encrypt ACME. Wildcard certificates (`*.lcat.dev`) are issued once and shared across apps via `secretKeyRef` in Ingress resources.
- **Kustomize:** Manifests use Kustomize for overlays, allowing production-specific configuration without code duplication.

