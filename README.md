# MasterBlaster-Control • Kali MCP Nexus v1.1 (Usable Orchestration Control Plane)

Professional desktop GUI Control Plane that orchestrates the 20+ MCPs from the MasterBlaster engine.

## Features (v1.1 - Usable Product)
- Full PySide6 (Qt6) dark Kali-themed GUI
- 22 MCP tabs + expandable slots with parameter forms
- **Live Dashboard Cards**: All MCPs shown, real-time Idle/Running/Success/Failed/Stopped, color coding, progress bars. Clickable to jump to tab.
- **Functional Run All MCPs**: Sequential execution (completion-driven, not timers). Live card updates + aggregated results.
- **Global Stop All**: Cleanly terminates running processes, aborts batches/workflows, updates UI/cards.
- **Functional Workflow Builder**: Add/reorder/remove MCPs in right panel. Execute Chain runs in order with live status, logs, intel.
- Per-MCP **Stop** button + robust QProcess handling.
- **Demo-safe execution**: If Kali tools missing (Windows dev etc.), realistic simulated outputs per MCP type with parsed intel (ports, vulns, creds, etc.).
- Universal log + Target Intel panel with automatic aggregation.
- Evidence collector + full Export (menu) with watermarked Markdown reports.
- “Verify & Install All Kali Tools” button (real PATH check + demo notes).
- Ethics & legal banner + watermark toggle in Settings.
- Polish: status bar, global target sync across tabs, button state management.

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
pip install pyside6 pyyaml
python main.py
```

**Note**: Runs on any OS. On non-Kali hosts, missing tools auto-use realistic demo/simulated output so you can test the full orchestration, dashboard, Run All, Workflows, Stop, and exports immediately.

See the full push sequence in the generation.

## 22 MCPs (20 + 2 expandable slots)
1. Recon-Nmap MCP
2. Recon-Maltego OSINT MCP
3. Vuln-OpenVAS MCP
4. Vuln-Nikto Web MCP
5. Web-Burp Suite Proxy MCP
6. Web-SQLMap MCP
7. Web-Gobuster Hybrid MCP
8. Exploit-Metasploit Framework MCP
9. Exploit-SET Social-Engineering MCP
10. Wireless-Aircrack-ng Suite MCP
11. Wireless-Bettercap MITM MCP
12. Wireless-Yersinia Layer2 MCP
13. Password-John + Hashcat Hybrid MCP
14. Password-Hydra Brute MCP
15. Password-Responsive LLMNR MCP
16. Post-Empire MCP
17. Forensics-Autopsy + Volatility MCP
18. Forensics-Foremost Carver MCP
19. Sniff-Wireshark + tcpdump MCP
20. Reporting-Dradis + Export MCP
21. Future MCP 21 (Expandable)
22. Future MCP 22 (Expandable)

## Ethics
See ethics.md

For authorized use only.

## Bonus Image Prompts (v1.1 Real Control Plane)
1. Professional dark Kali Linux desktop GUI MasterBlaster-Control v1.1, top bar with logo and global target, left sidebar 22 MCP buttons with live colored status dots (gray/green/yellow/red), central dashboard with full grid of 22 live cards showing Running/Success/Failed/Stopped with progress bars, right workflow chain list with up/down/remove and Execute button, modern cyber UI, 4K
2. Detailed PySide6 MCP tab for SQLMap in dark theme: parameter form, big Execute and Stop buttons, live scrolling terminal output, progress bar, parsed results table showing found vulnerabilities, status badges
3. Interactive workflow builder canvas in MasterBlaster-Control: draggable MCP nodes (Nmap, SQLMap, Metasploit) connected in sequence, global target, live execution status glow on current step, dark Kali aesthetic with universal log below

```

**2. .gitignore** (write it)