#!/usr/bin/env python3
"""
Generate ArgoCD Application manifests from declarative config.
This script is the source of truth generator for all Application definitions.

Usage:
  python3 scripts/generate-argocd-apps.py

This reads argocd/apps/config.yaml and generates individual Application manifest
files, eliminating boilerplate and making it easy to add new applications.

To add a new application:
1. Add entry to argocd/apps/config.yaml
2. Run this script
3. Commit the generated YAML files
"""

import yaml
import sys
from pathlib import Path

CONFIG_FILE = "argocd/apps/config.yaml"
OUTPUT_DIR = "argocd/apps"

def load_config(config_path):
    """Load application definitions from config.yaml"""
    with open(config_path) as f:
        return yaml.safe_load(f)

def generate_application(app_config):
    """Generate Application manifest for a single app"""
    name = app_config["name"]
    description = app_config["description"]
    wave = app_config["wave"]
    repo_url = app_config["repoURL"]
    target_revision = app_config["targetRevision"]
    path = app_config["path"]
    namespace = app_config["namespace"]
    ingress = app_config.get("ingress")
    depends_on = app_config.get("dependsOn")
    
    # Build info array with dynamic entries
    info_items = [
        {"name": "Wave", "value": str(wave)},
        {"name": "Description", "value": description}
    ]
    
    if ingress:
        info_items.append({"name": "Ingress", "value": ingress})
    
    if depends_on:
        info_items.append({"name": "Depends on", "value": depends_on})
    
    app = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Application",
        "metadata": {
            "name": name,
            "namespace": "argocd",
            "annotations": {
                "kubernetes.io/description": description
            }
        },
        "spec": {
            "project": "homelab",
            "source": {
                "repoURL": repo_url,
                "targetRevision": target_revision,
                "path": path
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": namespace
            },
            "syncPolicy": {
                "automated": {
                    "prune": True,
                    "selfHeal": True
                },
                "syncOptions": ["CreateNamespace=true"],
                "retry": {
                    "limit": 5,
                    "backoff": {
                        "duration": "5s",
                        "factor": 2,
                        "maxDuration": "3m"
                    }
                }
            },
            "info": info_items
        }
    }
    
    return app

def generate_root_app(config):
    """Generate root app-of-apps orchestrator from config"""
    
    # Build wave structure documentation
    waves = {}
    for app in config["applications"]:
        wave = app["wave"]
        if wave not in waves:
            waves[wave] = []
        waves[wave].append(app["name"])
    
    # Build description with wave breakdown
    wave_lines = []
    for wave_num in sorted(waves.keys()):
        apps = waves[wave_num]
        wave_lines.append(f"      Wave {wave_num}: {', '.join(apps)}")
    
    description_parts = [
        "Root application orchestrator (app-of-apps pattern).",
        "Syncs all child applications in dependency order across waves:"
    ] + wave_lines
    
    root_app = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Application",
        "metadata": {
            "name": "root",
            "namespace": "argocd",
            "annotations": {
                "kubernetes.io/description": "\n".join(description_parts)
            }
        },
        "spec": {
            "project": "homelab",
            "source": {
                "repoURL": "https://github.com/lc-at/-kates.git",
                "targetRevision": "main",
                "path": "argocd/apps"
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": "argocd"
            },
            "syncPolicy": {
                "automated": {
                    "prune": True,
                    "selfHeal": True
                },
                "syncOptions": ["CreateNamespace=true"],
                "retry": {
                    "limit": 5,
                    "backoff": {
                        "duration": "5s",
                        "factor": 2,
                        "maxDuration": "3m"
                    }
                }
            },
            "info": [
                {"name": "Pattern", "value": "App-of-Apps"},
                {"name": "Type", "value": "Orchestrator"},
                {"name": "Total Applications", "value": str(len(config["applications"]))}
            ]
        }
    }
    
    return root_app

def write_application(app_dict, app_name):
    """Write Application to YAML file"""
    output_path = Path(OUTPUT_DIR) / f"{app_name}.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(app_dict, f, default_flow_style=False, sort_keys=False, width=120)
    return output_path

def main():
    # Load config
    config = load_config(CONFIG_FILE)
    
    generated_files = []
    
    # Generate root app first
    root_app = generate_root_app(config)
    root_path = write_application(root_app, "root")
    generated_files.append(root_path)
    print(f"✓ Generated: {root_path}")
    
    # Generate child applications
    for app_config in config["applications"]:
        app_manifest = generate_application(app_config)
        app_name = app_config["name"]
        output_path = write_application(app_manifest, app_name)
        generated_files.append(output_path)
        print(f"✓ Generated: {output_path}")
    
    print(f"\n✓ Generated {len(generated_files)} Application manifests from {CONFIG_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
