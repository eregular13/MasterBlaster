# MasterBlaster v1.0 Live Demo Video Script

**Duration:** 4–5 minutes  
**Tone:** Professional, security-first, no hype about "hacking"

## Scene 1 — Cold open (0:00–0:30)

- Show desktop with MasterBlaster window: title bar **v1.0 — Authorized Assessment Control Plane**
- Voiceover: "This is not a live pentest box. It's a deny-by-default control plane for authorized assessment simulation."

## Scene 2 — Ethics gate (0:30–0:45)

- Click Help → Ethics, accept disclaimer
- Highlight **DENY BY DEFAULT** badge

## Scene 3 — Engagement + target (0:45–1:15)

- Set target `example.com`, pick engagement from combo
- Open Records browser tab briefly

## Scene 4 — Simulator run (1:15–2:00)

- Select A0 adapter, run simulator job
- Show approval flow if prompted
- Point to audit log and fixture evidence — no network calls

## Scene 5 — Guardrails panel (2:00–2:45)

- P0 Guardrails → Plugin Catalog, Generate Workflow Draft, Enrich with Assistant
- Hot-Reload Plugins, Plugin Review Queue
- Phase Roadmap P0–P10

## Scene 6 — Exports (2:45–3:30)

- File → Export Compliance Draft, Workflow Draft, Assistant Enrichment
- Show watermark disclaimer on markdown export

## Scene 7 — MCP + CI (3:30–4:15)

- Terminal: `echo '{"method":"ping"}' | python scripts/mcp_stdio_server.py`
- Mention GitHub release v1.0.0, SBOM artifact, pytest 99+

## Close (4:15–4:30)

- "Star the repo if you believe security tooling should fail closed."
- URL: https://github.com/eregular13/MasterBlaster/tree/grok/masterblaster