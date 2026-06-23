# MasterBlaster Plugin Marketplace (Skeleton)

Community plugin listings are manifest-only in v1.0. No remote install or execution.

## Layout

- `catalog.json` — reviewed listing index (P10 skeleton)
- `submissions/` — community submission queue (see `docs/community/PLUGIN_SUBMISSION.md`)

## Validate

```bash
python scripts/validate_plugin_submission.py
```

Enable marketplace UI: set `MB_FEATURE_PLUGIN_MARKETPLACE=true` or edit `data/feature_flags.json`.