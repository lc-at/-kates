# TODO

## High-impact repository improvements

1. Add a root `README.md` describing architecture, namespaces, deploy order, and recovery steps.
2. Add `.gitignore` for local/dev files (`.kube/`, editor files, temp outputs, local kubeconfigs).
3. Pin and document all remote manifests (cert-manager and sealed-secrets versions are good; keep this pattern everywhere).
4. Split app manifests into smaller files (`namespace`, `secret/sealedsecret`, `db`, `app`, `service`, `ingress`) for easier review and safer rollbacks.
5. Add policy/validation in CI:
   - `kustomize build` for each stack
   - schema validation (`kubeconform` or `kubeval`)
   - policy checks (`conftest`/OPA or Kyverno CLI)
6. Standardize overlays:
   - `base/*`
   - `overlays/prod/*`
   - optional `overlays/staging/*`
7. Move all sensitive config to SealedSecrets (already done for `acme-dns`, continue for app creds).
8. Add backup/restore runbooks and scripts (Postgres/MariaDB dumps + PVC data procedures).
9. Add observability basics (metrics/logging/alerting docs, cert expiration alerting).
10. Add resource requests/limits and PodDisruptionBudget/anti-affinity where needed.
11. Reduce duplicate Let's Encrypt issuance for wildcard TLS:
   - today each namespace has its own wildcard `Certificate`, which causes duplicate issuance/renewal
   - evaluate issuing once in a single namespace and syncing/copying TLS secret to other namespaces (e.g., reflector/external-secrets approach)

## ArgoCD GitOps rollout plan

## Phase 1: Prepare repo structure for GitOps

1. ✓ Create `base` and `overlays/prod`.
2. ✓ Convert current manifests into Kustomize bases + prod overlay patches.
3. ✓ Keep cluster bootstrap components separated:
   - `bootstrap/sealed-secrets`
   - `bootstrap/cert-manager`
4. ✓ Ensure all secrets in Git are SealedSecrets only.
5. ✓ Create app-of-apps ArgoCD definitions:
   - `argocd/project-homelab.yaml` — AppProject with RBAC scoping
   - `argocd/apps/root.yaml` — Root app-of-apps orchestrator
   - `argocd/apps/bootstrap-sealed-secrets.yaml` — Wave 0
   - `argocd/apps/bootstrap-cert-manager-install.yaml` — Wave 1
   - `argocd/apps/platform-cert-manager-config.yaml` — Wave 2
   - `argocd/apps/miniflux.yaml` — Wave 3
   - `argocd/apps/wallabag.yaml` — Wave 3
6. ✓ Move wildcard Certificates from cert-manager-config into app overlays for namespace isolation.

## Phase 2: Install ArgoCD

1. Install ArgoCD in `argocd` namespace.
2. Expose ArgoCD UI/API (Ingress with TLS).
3. Configure repository credentials and project boundaries.

## Phase 3: Bootstrap applications

1. Create an app-of-apps root Application (or ApplicationSet).
2. Add child Applications in this order:
   - sealed-secrets controller
   - cert-manager install
   - cert-manager issuers/certificates
   - miniflux stack
   - wallabag stack
3. Use sync waves to enforce order.

## Phase 4: Guardrails and operations

1. ✓ Enable automated sync with `prune: true` and `selfHeal: true` for stable apps.
2. ✓ Add `syncOptions` (`CreateNamespace=true`, `ServerSideApply=true` where suitable).
3. ✓ Define ArgoCD Projects to limit namespace/cluster-scoped resource access.
4. Add PR checks that run the same Kustomize build/validation used in GitOps.
5. Document incident flow: pause sync, rollback to git SHA, resume sync.

## Initial ArgoCD manifests to add

_(All complete - see `argocd/` directory)_
