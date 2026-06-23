# MasterBlaster Docs Site (Scaffold)

Welcome to the MasterBlaster Authorized Security Assessment Control Plane documentation scaffold.

## Sections

- [P0 Acceptance Checklist](../P0_ACCEPTANCE_CHECKLIST.md)
- [Review Policy](../REVIEW_POLICY.md)
- [Security Impact](../SECURITY_IMPACT.md)
- [Threat Model Impact](../THREAT_MODEL_IMPACT.md)
- [Plugin System Design](../design/plugin-system.md)
- [AI Workflow Generator](../design/ai-workflow-generator.md)
- [v1.0 Release Checklist](../V1_RELEASE_CHECKLIST.md)

## Quick Links

| Topic | Path |
| --- | --- |
| Run desktop UI | `python main.py` |
| Run tests | `python -m pytest` |
| Console demo | `python scripts/demo_p0_overdrive.py` |
| Docker demo | `docker compose up --build` |

## Roadmap

See `masterblaster_control/phase_tracker.py` for the live P0-P9 phase dashboard rendered in report exports.