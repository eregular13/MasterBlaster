# Plugin System Design (P7)

## Goal

Allow third-party **reviewed adapters** and **non-executing resources** to register without modifying core runner code.

## Architecture

```text
PluginManifest (signed, versioned)
    -> PluginRegistry (deny-by-default lookup)
        -> RunnerSimulator (execution boundary)
        -> p0_resources (read-only templates)
```

## Plugin Contract

| Field | Requirement |
| --- | --- |
| `plugin_id` | Stable identifier |
| `adapter_manifests` | Reviewed, fixture-only until approved phase |
| `resources` | Non-executing URIs only |
| `min_core_version` | Semantic compatibility gate |

## Loading Model (v1.0 target)

1. Discover plugins from `plugins/` directory
2. Validate manifest schema + review flag
3. Register into in-memory registry at startup
4. Refuse plugins requesting network transport in P0-P2

## Security

- Plugins cannot override policy, approvals, or signing
- Plugins cannot write signing keys or mutate RBAC
- Unsigned plugins blocked in production mode

## Milestones

- [ ] Manifest schema + validator CLI
- [ ] Hot-reload in dev mode only
- [ ] Marketplace metadata format (out of band)