# ADR 0003: v2 Plugin Marketplace Governance

## Status

Proposed (P10 scaffold)

## Context

P7 loads reviewed non-executing plugins from `plugins/`. Community demand requires a submission queue without introducing remote code execution.

## Decision

1. Submissions land in `marketplace/submissions/<id>/` with `plugin.json` + `submission.json`.
2. Maintainers promote approved manifests to `plugins/` after security review.
3. `catalog.json` is a read-only listing index — no installer, no auto-load.
4. Feature flag `plugin_marketplace` gates UI surfaces.
5. `validate_plugin_submission.py` runs in CI on queue changes.

## Consequences

- Community plugins cannot execute until reviewed and copied into `plugins/`.
- Marketplace is manifest metadata only in v1.x.
- v2 may add signed manifest bundles with provenance attestations.