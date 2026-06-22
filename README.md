# MasterBlaster-Control • Kali MCP Nexus v1.0

Professional desktop GUI Control Plane that orchestrates the 20+ MCPs from the MasterBlaster engine.

## Features
- Full PySide6 (Qt6) dark Kali-themed GUI
- Git submodule integration with MasterBlaster (core engine)
- Dedicated "MasterBlaster Direct" tab for one-click launch of any script from the submodule
- Bidirectional target/results piping between GUI MCPs and MasterBlaster
- 20 rich MCP tabs + 2 expandable slots
- Dashboard grid with live status cards
- Per-MCP parameter forms, presets, Execute button, live output pane, charts
- Bottom: Universal log + evidence collector
- Right: Target intel + quick workflow builder (drag-drop MCP chain)
- Extra tab: “MasterBlaster Bridge” — full control over the original repo’s functions
- “Verify & Install All Kali Tools” button
- Ethics & legal banner with acknowledgment
- Watermark toggle for reports

## Tech Stack
- Primary: Python 3.12 + PySide6 (Qt6) native desktop GUI (dark Kali theme)
- Execution: subprocess + QProcess + embedded terminal panes
- Interoperability: git submodule for MasterBlaster + Python import or CLI calls
- Database: SQLite + optional export to Dradis
- Packaging: PyInstaller one-click .deb + AppImage ready

## Kali Tools
All tools are from standard Kali Linux 2026 repositories.

Use the "Verify & Install All Kali Tools" button or run:

```bash
./scripts/verify_kali_tools.sh
```

## Quick Start

```bash
git clone https://github.com/eregular13/MasterBlaster.git
cd MasterBlaster
git submodule update --init --recursive
chmod +x setup.sh
./setup.sh
python main.py
```

See the full push sequence in the generation.

## 20 MCPs
1. Recon-Nmap MCP
... (list as before)

## Ethics
See ethics.md

For authorized use only.

## Bonus Image Prompts
1. Professional dark Kali Linux desktop GUI called MasterBlaster-Control, top bar with logo and global target input, left sidebar with 20 MCP status cards, central dashboard grid of colorful status cards, modern flat cyber design, high contrast, 4K resolution
2. PySide6 dark theme tab for Recon-Nmap MCP inside MasterBlaster-Control. Left: clean form with Target, Ports, Flags. Center: big green Execute button. Right: live terminal output. Bottom: results table. Professional pentest tool aesthetic
3. Dark cybersecurity workflow canvas in MasterBlaster-Control. Drag-drop nodes for different MCPs connected by arrows, target flow, evidence collector on right. Clean modern UI, Kali color palette

```

**2. .gitignore** (write it)