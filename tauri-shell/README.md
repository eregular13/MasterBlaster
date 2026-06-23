# MasterBlaster Tauri Shell (Scaffold)

Native desktop wrapper for the Python MCP command center.

## Architecture

```
Tauri WebView (Rust)  →  spawns  →  python main.py (PySide6 backend)
                  ↘  optional MCP HTTP on :8765
```

## Prerequisites

- [Rust](https://rustup.rs/) + [Tauri prerequisites](https://tauri.app/start/prerequisites/)
- Python 3.12+ with `requirements.txt` installed at repo root

## Dev workflow

```bash
# From repo root — start Python backend
python main.py

# From tauri-shell (when Rust toolchain installed)
cd tauri-shell
npm install
npm run tauri dev
```

## Build

```bash
cd tauri-shell
npm run tauri build
```

## v2 roadmap

- Embed Qt window handle or migrate UI to Tauri + web frontend
- Auto-start MCP HTTP server on launch
- System tray + engagement quick-switcher