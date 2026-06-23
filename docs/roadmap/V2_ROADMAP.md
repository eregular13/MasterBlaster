# MasterBlaster v2 Roadmap

## North star

Governed live adapters (A7+) with enterprise auth, HSM signing, and a reviewed plugin marketplace — while preserving deny-by-default simulator mode as the default boot path.

## v2 pillars

| Pillar | v1.0 | v2 target |
| --- | --- | --- |
| Execution | Simulator-only | Feature-flagged live transport with ROE + approval |
| Auth | Local users + OIDC scaffold | OIDC/OAuth2 with tenant RBAC |
| Keys | Local KeyStore | HSM + rotation audit trail |
| Integrations | MCP stdio + HTTP | MCP HTTP + webhook exports |
| Community | Plugin catalog | Marketplace with review queue |
| Distribution | PyInstaller CI | Code-signed Windows + macOS notarization |

## Milestones

1. **v1.1** — P9 complete, A7 behind flag, release automation
2. **v1.5** — OIDC login, plugin marketplace beta
3. **v2.0** — Governed A7, HSM signing, certified installer channel