# Changelog

## [1.0.0] - 2026-06-23

### Added
- MasterBlaster Authorized Security Assessment Control Plane on `grok/masterblaster`
- Seven reviewed simulator-only adapters (A0–A6) with mock transport and rate limiting
- Records browser with CRUD, audit/evidence export, and deep-links
- Compliance draft generator with findings projection
- Persistent signing keys, RBAC roles, and filtered audit export
- P7 plugin loader with non-executing manifest validation
- Deterministic AI workflow draft generator (non-executing planning artifact)
- P8 enterprise horizon: MCP stdio/HTTP, local auth, hot-reload, pen-test pack, Pages CI
- P9 scaffolds: feature flags, HSM keystore, OIDC auth, A7 gated adapter, plugin review queue
- P10 scaffolds: marketplace catalog, v2 roadmap, live demo video script, Discord scaffold
- Docker, PyInstaller spec, Windows signing scaffold, multi-platform CI, SBOM tooling
- Release notes automation and official v1.0.0 GitHub Release assets
- Community assets: CONTRIBUTING, issue templates, docs site, star campaign

### Security
- Deny-by-default policy, human approval gate, signed expiring job envelopes
- Adversarial pen-test pack and parse-target fuzz regression tests
- No live network transport or host command execution in v1.0 simulator mode

[1.0.0]: https://github.com/eregular13/MasterBlaster/releases/tag/v1.0.0