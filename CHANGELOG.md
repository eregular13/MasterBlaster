# Changelog

## [1.1.0] - 2026-06-22

### Added
- Professional business layer: client/project management, engagement templates, assessment pipelines
- Client-facing report generator with executive summary, severity ratings, remediation, compliance appendix
- Findings-to-proposal generator for consulting upsell workflows
- Usage logging and billing CSV export
- CRM-friendly findings CSV and report JSON export
- Clients & Projects UI tab with one-click report and proposal generation
- Firm branding configuration (`data/business/firm_config.json`)
- CLI: `scripts/generate_client_report.py`

### Changed
- README and ethics rewritten for professional consulting use case
- UI rebranded for enterprise assessment workflows (Deliverables menu, professional terminology)

[1.1.0]: https://github.com/eregular13/MasterBlaster/releases/tag/v1.1.0

## [1.0.0-warlord] - 2026-06-22

### Added
- **Kali tool wrappers** (`kali_tool_wrappers.py`) — 17 governed tools with assault presets
- **CLI `unleash_arsenal.py`** — `--tool`, `--preset`, `--category`, `--all` flags
- **Tool Arsenal tab** — visual grid with one-click UNLEASH buttons per tool
- **Warlord Command Deck** — big red CRACK THE WHIP button, live strike counter, success pulse animations
- **Total Annihilation Mode** — zero-delay 22-MCP queue + tool barrage after each strike
- **War Packs marketplace** — 7 pre-configured MCP + tool chains (`marketplace/war_packs.json`)
- Savage v1.0 release assets: demo video script, announcement post, release notes

### Changed
- ethics.md and README rewritten as weapon-grade doctrine — governed, not neutered
- Command Post tab renamed; marketplace markdown shows War Packs

[1.0.0-warlord]: https://github.com/eregular13/MasterBlaster/releases/tag/v1.0.0-warlord

## [2.1.0-warlord] - 2026-06-22

### Added
- MasterBlaster WARLORD rebrand on `grokier/masterblaster` — 22 MCP command plane
- Kali-grade tool arsenal (`mcp_tool_arsenal.py`) — 67 tool bindings across all MCP slots
- Warlord assault-chain orchestrator with per-step approval and evidence capture
- Default 8-MCP strike chain and 12-MCP full assault chain (recon → network → web → API → evidence)
- Savage demo scripts: `demo_warlord_chain.py`, `demo_warlord_full_chain.py`
- Warlord menu in GUI: crack chains, export Markdown reports and JSON telemetry
- Warlord Command Post UI: arsenal catalog, Kali bindings, assault chain buttons

### Changed
- README, ethics.md, and marketing rewritten for warlord tone — capable and governed, not neutered
- Smart governance retained: authorized engagements, scope lock, human approval, signed jobs, audit trail

### Security
- Orchestrated fixture/mock transport — no raw subprocess execution in core control plane
- Policy gate and approval envelope on every MCP strike in the chain

[2.1.0-warlord]: https://github.com/eregular13/MasterBlaster/releases/tag/v2.1.0-warlord

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