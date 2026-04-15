# k8s-aurel

Kubernetes manifests for the Aurel homelab cluster (k3s), including Miniflux, Wallabag, cert-manager, and Sealed Secrets.

## Repository layout

- `bootstrap/`: cluster bootstrap components (install controllers/operators first).
- `base/`: reusable base manifests for workloads and shared config.
- `overlays/prod/`: production composition used for GitOps sync targets.

## Namespaces

- `cert-manager`: cert-manager and ACME account/solver secrets.
- `miniflux`: Miniflux app and PostgreSQL.
- `wallabag`: Wallabag app, MariaDB, and Redis.

## Deploy order

1. Bootstrap controllers:
   - `kubectl apply -k bootstrap/sealed-secrets/install`
   - `kubectl apply -k bootstrap/cert-manager/install`
2. Apply production overlay:
   - `kubectl apply -k overlays/prod`

## Validation

Build and inspect before applying:

```bash
kubectl kustomize bootstrap
kubectl kustomize overlays/prod
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
