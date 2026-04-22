# Copilot Instructions for `k8s-aurel`

## Build, test, and lint commands

This repository has no application build/lint/test toolchain; it contains Kubernetes manifests and Docker Compose references.

Use these commands as the required validation workflow:

```bash
# Validate one Kubernetes manifest file (single-file check)
kubectl kustomize apps/miniflux

# Validate all Kubernetes manifests
kubectl kustomize bootstrap >/tmp/bootstrap.yaml && \
kubectl kustomize config >/tmp/config.yaml && \
kubectl kustomize apps >/tmp/apps.yaml

# Validate one Compose reference file (single-file check)
docker compose -f composes_ref/miniflux/compose.yaml config -q

# Validate all Compose reference files
docker compose -f composes_ref/miniflux/compose.yaml config -q && \
docker compose -f composes_ref/wallabag/compose.yml config -q && \
docker compose -f composes_ref/caddy/compose.yml config -q
```

## High-level architecture

The project is a Compose-to-Kubernetes migration for two self-hosted apps:

- **Miniflux stack**: app + PostgreSQL (`base/miniflux/*`, `apps/miniflux/*`)
- **Wallabag stack**: app + MariaDB + Redis (`base/wallabag/*`, `apps/wallabag/*`)

Each stack exposes an app Service and an Ingress, and each has a separate Secret manifest used by Deployments through `secretKeyRef`.

`composes_ref/*` is the migration reference for runtime behavior (images, env vars, network assumptions, reverse proxy routes). Kubernetes manifests should preserve functional parity with these references while using Kubernetes-native patterns.

## Key conventions for this repository

Follow Kubernetes best practices for all edits, even if existing manifests are less strict:

1. Prefer stable APIs and controller-managed workloads (`Deployment`, `StatefulSet`, `Job`), never naked Pods.
2. Use Kubernetes DNS service discovery (Service names), not Pod IPs or host networking shortcuts.
3. Keep manifests minimal, explicit, and YAML-first; avoid redundant defaults and avoid ambiguous YAML boolean forms.
4. Use consistent, semantic labels on all resources, including recommended `app.kubernetes.io/*` labels.
5. Add useful annotations (especially `kubernetes.io/description`) when creating or significantly changing resources.
6. Keep secrets out of plain values in workload manifests; use Secret refs and maintain clear secret ownership per app.
7. Preserve migration parity: when changing Kubernetes env vars/ports/domains, verify corresponding behavior in `composes_ref/*` and keep intent aligned.

When making larger changes, prefer validating by Kustomize app (`apps/miniflux/`, `apps/wallabag/`) so related resources evolve together.
