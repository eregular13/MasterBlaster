# Community Plugin Submission Workflow

MasterBlaster v1.0 accepts **non-executing, reviewed** plugin manifests only.

## Steps

1. Fork `grok/masterblaster` and create a branch.
2. Add your manifest under `marketplace/submissions/<your-plugin>/plugin.json`.
3. Add `submission.json` with `submitter`, `state` (`pending`), and `notes`.
4. Run `python scripts/validate_plugin_submission.py`.
5. Open a PR using `.github/pull_request_template.md` — security review required.

## Requirements

- `schema_version`: `1.0`
- `non_executing`: `true`
- `reviewed`: `false` until maintainers approve
- No shell execution, network calls, or subprocess imports in plugin code paths

## Review queue

The Guardrails panel **Plugin Review Queue** button renders `p9_plugin_review.review_queue_markdown()`.