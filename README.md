# MasterBlaster Authorized Security Assessment Control Plane

MasterBlaster is an authorized security assessment control plane that progresses through phased delivery from a deny-by-default simulator (P0) to a community-ready platform (P7).

**Current branch:** `feature/p0-continuation` — P0-P7 roadmap modules implemented; simulator-first invariants preserved.

## Capabilities

| Phase | Highlights |
| --- | --- |
| **P0** | 100% acceptance — reviewed manifests, policy gate, signed jobs, fixture evidence |
| **P1** | CRUD forms, engagement picker, retention presets, Records browser |
| **P2** | Mock transport, rate-limit simulator, A5/A6 adapters |
| **P3** | Findings projection, compliance draft generator (JSON/Markdown) |
| **P4** | Persistent signing keys, RBAC roles, filtered audit export |
| **P5** | Docker, PyInstaller spec, multi-platform CI matrix |
| **P6** | CONTRIBUTING, issue templates, docs site scaffold |
| **P7** | Plugin system + AI workflow design docs, v1.0 checklist |

## Adapters (7 reviewed, simulator-only)

- `a0.fixture.inventory` — offline inventory fixture
- `a1.tls.assessment` — TLS parser, fake/mock transport
- `a2.dns.posture` — DNS posture fixture
- `a3.http.headers` — HTTP security headers fixture
- `a4.tls.cert_expiry` — certificate expiry fixture
- `a5.port.scan_sim` — P2 mock port scan
- `a6.web.crawl_sim` — P2 mock web crawl

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m pytest
python main.py
```

Console demo:

```bash
python scripts/demo_p0_overdrive.py
```

Docker:

```bash
docker compose up --build
```

## Desktop UI

- **Dashboard** — live adapter cards
- **Simulator tabs** — per-adapter runs with human approval gate
- **Records** — CRUD, audit/evidence browser, exports, deep-links
- **Guardrails** — acceptance + phase dashboards
- **File menu** — report + compliance draft exports

## Security Notes

- No live network transport or host command execution in current phases
- UI is not a trusted authorization boundary
- Reports are drafts — not compliance certification
- See `docs/REVIEW_POLICY.md` and `ethics.md`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security-sensitive paths require review per `.github/CODEOWNERS`.

## Roadmap Docs

- [Plugin System](docs/design/plugin-system.md)
- [AI Workflow Generator](docs/design/ai-workflow-generator.md)
- [v1.0 Release Checklist](docs/V1_RELEASE_CHECKLIST.md)
- [Docs Site Scaffold](docs/site/index.md)