# masterblaster_control/main_window.py
# Updated for v1.1: Live dashboard cards, Run All + Stop All, functional workflow builder,
# improved MCPTab integration with status callbacks, polish.

import os
import sys
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSplitter, QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QPushButton, QTextEdit, QProgressBar, QMenuBar, QStatusBar,
    QMessageBox, QCheckBox, QFileDialog, QGridLayout, QFrame, QPlainTextEdit, QComboBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QProcess, QSettings, QTimer
from PySide6.QtGui import QFont, QAction
from .mcp_definitions import MCPS, get_mcp_by_id
from .mcp_tab import MCPTab
from .masterblaster_bridge import MasterBlasterBridge
from .utils import dark_kali_stylesheet, ensure_dirs, write_watermarked_report

class DashboardCard(QFrame):
    """Live status card for dashboard. Clickable to jump to MCP tab."""
    def __init__(self, mcp_id, name, on_click=None, parent=None):
        super().__init__(parent)
        self.mcp_id = mcp_id
        self.name = name
        self.status = "Idle"
        self.progress = 0
        self.on_click = on_click

        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("QFrame { background: #2a2a2a; border: 1px solid #444; border-radius: 6px; }")
        lay = QVBoxLayout(self)

        self.title = QLabel(f"<b>{name}</b>")
        lay.addWidget(self.title)

        self.status_label = QLabel("● Idle")
        self.status_label.setStyleSheet("color: #888;")
        lay.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(8)
        lay.addWidget(self.progress_bar)

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.mcp_id)
        super().mousePressEvent(event)

    def update_status(self, status, progress=0):
        self.status = status
        self.progress = progress
        color = {
            "Idle": "#888",
            "Running": "#ffaa00",
            "Success": "#00ff9d",
            "Failed": "#ff4444",
            "Stopped": "#ff8800"
        }.get(status, "#888")
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"color: {color};")
        self.progress_bar.setValue(progress)
        if status == "Running":
            self.setStyleSheet("QFrame { background: #2a2a2a; border: 2px solid #ffaa00; border-radius: 6px; }")
        elif status == "Success":
            self.setStyleSheet("QFrame { background: #2a2a2a; border: 1px solid #00ff9d; border-radius: 6px; }")
        elif status == "Failed":
            self.setStyleSheet("QFrame { background: #2a2a2a; border: 1px solid #ff4444; border-radius: 6px; }")
        elif status == "Stopped":
            self.setStyleSheet("QFrame { background: #2a2a2a; border: 2px solid #ff8800; border-radius: 6px; }")
        else:
            self.setStyleSheet("QFrame { background: #2a2a2a; border: 1px solid #444; border-radius: 6px; }")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MasterBlaster-Control • Kali MCP Nexus v1.1")
        self.resize(1450, 950)
        self.settings = QSettings("MasterBlaster", "Control")
        self.global_target = ""
        self.running_processes = {}  # mcp_id -> QProcess
        self.watermark_enabled = self.settings.value("watermark", True, type=bool)
        self.ethics_accepted = self.settings.value("ethics_accepted", False, type=bool)

        self.dashboard_cards = {}  # mcp_id -> DashboardCard
        self.workflow_chain = []   # list of mcp_ids

        # Batch Run All state (Phase 3)
        self._batch_running = False
        self._batch_queue = []

        # Workflow state (Phase 4)
        self._workflow_running = False
        self._workflow_queue = []
        self._current_workflow_step = None

        self._init_ui()
        self._apply_dark_theme()
        self._check_ethics()
        self._load_masterblaster_submodule()
        self._update_status("Ready • v1.1 Real Control Plane")

    def _init_ui(self):
        # TOP BAR (same as before, plus more)
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)

        logo = QLabel("🛡️ MasterBlaster-Control v1.1")
        logo.setFont(QFont("Consolas", 18, QFont.Bold))
        logo.setStyleSheet("color: #00ff9d;")
        top_layout.addWidget(logo)

        control_badge = QLabel("REAL CONTROL PLANE")
        control_badge.setStyleSheet("background: #ff4444; color: white; padding: 2px 8px; border-radius: 3px; font-size: 10pt;")
        top_layout.addWidget(control_badge)

        top_layout.addSpacing(20)

        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Global Target (e.g. 192.168.1.1 or example.com)")
        self.target_edit.setMinimumWidth(300)
        self.target_edit.textChanged.connect(self._on_global_target_changed)
        top_layout.addWidget(self.target_edit, 4)

        self.kali_btn = QPushButton("🔧 Verify & Install All Kali Tools")
        self.kali_btn.clicked.connect(self._verify_and_install_kali_tools)
        self.kali_btn.setStyleSheet("background: #ffaa00; color: black;")
        top_layout.addWidget(self.kali_btn)

        self.run_all_btn = QPushButton("▶ Run All MCPs")
        self.run_all_btn.clicked.connect(self._run_all_mcps)
        top_layout.addWidget(self.run_all_btn)

        self.stop_all_btn = QPushButton("⏹ Stop All")
        self.stop_all_btn.clicked.connect(self._stop_all)
        self.stop_all_btn.setEnabled(False)
        top_layout.addWidget(self.stop_all_btn)

        self.setMenuBar(QMenuBar())
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("Export All Reports", self._export_all_reports)
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("Ethics", lambda: self._show_ethics_dialog(force=True))
        help_menu.addAction("About", self._show_about)

        # CENTRAL SPLITTER
        central_splitter = QSplitter(Qt.Horizontal)

        # LEFT SIDEBAR
        sidebar = QWidget()
        sidebar.setMinimumWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(5, 5, 5, 5)

        mcp_label = QLabel(f"MCPs ({len(MCPS)})")
        mcp_label.setFont(QFont("Consolas", 11, QFont.Bold))
        side_layout.addWidget(mcp_label)

        self.mcp_list = QListWidget()
        self.mcp_list.setMaximumWidth(220)
        self.mcp_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.mcp_list.setMinimumHeight(450)
        for mcp in MCPS:
            item = QListWidgetItem(f"  {mcp['name']}")
            item.setData(Qt.UserRole, mcp['id'])
            self.mcp_list.addItem(item)
        self.mcp_list.currentItemChanged.connect(self._on_mcp_selected)
        side_layout.addWidget(self.mcp_list)

        side_layout.addSpacing(15)
        mb_label = QLabel("MasterBlaster Engine")
        mb_label.setFont(QFont("Consolas", 11, QFont.Bold))
        side_layout.addWidget(mb_label)

        self.mb_direct_btn = QPushButton("MasterBlaster Direct")
        self.mb_direct_btn.clicked.connect(self._switch_to_masterblaster_bridge)
        self.mb_direct_btn.setStyleSheet("background: #00aa66;")
        side_layout.addWidget(self.mb_direct_btn)

        central_splitter.addWidget(sidebar)

        # MAIN TABS
        self.main_tabs = QTabWidget()

        # Dashboard with live cards
        self.dashboard = self._build_live_dashboard()
        self.main_tabs.addTab(self.dashboard, "📊 Dashboard")

        # Dynamic MCP Tabs
        self.mcp_tab_widgets = {}
        for mcp in MCPS:
            tab = MCPTab(mcp, self)
            self.mcp_tab_widgets[mcp['id']] = tab
            self.main_tabs.addTab(tab, mcp['name'].split()[0])

        # MasterBlaster Bridge
        self.mb_bridge = MasterBlasterBridge(self)
        self.main_tabs.addTab(self.mb_bridge, "🔧 MasterBlaster Direct")

        central_splitter.addWidget(self.main_tabs)
        central_splitter.setStretchFactor(1, 4)

        # Set reasonable initial sizes for sidebar | main | right panel
        central_splitter.setSizes([240, 850, 280])

        # RIGHT PANEL - Workflow Builder (now functional)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("Target Intel"))
        self.intel_edit = QTextEdit()
        self.intel_edit.setReadOnly(True)
        right_layout.addWidget(self.intel_edit)

        right_layout.addWidget(QLabel("Workflow Builder (v1.1)"))
        self.workflow_list = QListWidget()
        right_layout.addWidget(self.workflow_list)

        wf_btns = QHBoxLayout()
        self.add_mcp_combo = QComboBox()
        for mcp in MCPS:
            self.add_mcp_combo.addItem(mcp['name'], mcp['id'])
        wf_btns.addWidget(self.add_mcp_combo)
        self.add_to_chain_btn = QPushButton("Add to Chain")
        self.add_to_chain_btn.clicked.connect(self._add_to_workflow)
        wf_btns.addWidget(self.add_to_chain_btn)
        right_layout.addLayout(wf_btns)

        chain_btns = QHBoxLayout()
        self.up_btn = QPushButton("↑ Up")
        self.up_btn.clicked.connect(self._move_workflow_up)
        chain_btns.addWidget(self.up_btn)
        self.down_btn = QPushButton("↓ Down")
        self.down_btn.clicked.connect(self._move_workflow_down)
        chain_btns.addWidget(self.down_btn)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_from_workflow)
        chain_btns.addWidget(self.remove_btn)
        right_layout.addLayout(chain_btns)

        self.exec_workflow_btn = QPushButton("▶ Execute Workflow")
        self.exec_workflow_btn.clicked.connect(self._execute_workflow)
        right_layout.addWidget(self.exec_workflow_btn)

        self.clear_chain_btn = QPushButton("Clear Chain")
        self.clear_chain_btn.clicked.connect(self._clear_workflow)
        right_layout.addWidget(self.clear_chain_btn)

        central_splitter.addWidget(right_panel)

        # BOTTOM LOG
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        log_label = QLabel("Universal Log + Evidence Collector")
        bottom_layout.addWidget(log_label)

        self.universal_log = QPlainTextEdit()
        self.universal_log.setReadOnly(True)
        self.universal_log.setMaximumHeight(110)
        bottom_layout.addWidget(self.universal_log)

        self.collect_btn = QPushButton("Collect Current Output as Evidence")
        self.collect_btn.clicked.connect(self._collect_evidence)
        bottom_layout.addWidget(self.collect_btn)

        # FINAL LAYOUT
        main_v = QVBoxLayout()
        main_v.addWidget(top_bar)
        main_v.addWidget(central_splitter, 1)
        main_v.addWidget(bottom_widget)

        central = QWidget()
        central.setLayout(main_v)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready • v1.1 Real Control Plane - Live cards, Run All, Workflow active")

    def _apply_dark_theme(self):
        self.setStyleSheet(dark_kali_stylesheet())

    def _check_ethics(self):
        if self.ethics_accepted:
            return
        self._show_ethics_dialog()

    def _show_ethics_dialog(self, force=False):
        msg = QMessageBox(self)
        msg.setWindowTitle("ETHICS & LEGAL NOTICE")
        msg.setIcon(QMessageBox.Warning)
        text = "MasterBlaster-Control is for AUTHORIZED USE ONLY.\n\nYou must have explicit permission to test targets.\nUnauthorized use is illegal.\n\nDo you accept?"
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Accept | QMessageBox.Cancel)
        if msg.exec() == QMessageBox.Accept:
            self.ethics_accepted = True
            self.settings.setValue("ethics_accepted", True)
        else:
            if force:
                QMessageBox.critical(self, "Access Denied", "Must accept terms.")
            sys.exit(0)

    def _load_masterblaster_submodule(self):
        self.mb_submodule_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "MasterBlaster"))
        if os.path.isdir(self.mb_submodule_path):
            self.status_bar.showMessage("MasterBlaster submodule loaded.")
            if hasattr(self.mb_bridge, 'refresh_scripts'):
                self.mb_bridge.refresh_scripts()
        else:
            self.status_bar.showMessage("WARNING: MasterBlaster submodule not found.")

    def _build_live_dashboard(self):
        container = QWidget()
        lay = QGridLayout(container)
        lay.setSpacing(8)
        for idx, mcp in enumerate(MCPS):
            card = DashboardCard(mcp['id'], mcp['name'], on_click=self._switch_to_mcp)
            self.dashboard_cards[mcp['id']] = card
            row = idx // 4
            col = idx % 4
            lay.addWidget(card, row, col)
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(420)
        return scroll

    def _switch_to_mcp(self, mcp_id):
        if mcp_id in self.mcp_tab_widgets:
            self.main_tabs.setCurrentWidget(self.mcp_tab_widgets[mcp_id])

    def _on_mcp_selected(self, current, previous):
        if current:
            mcp_id = current.data(Qt.UserRole)
            if mcp_id and mcp_id in self.mcp_tab_widgets:
                self.main_tabs.setCurrentWidget(self.mcp_tab_widgets[mcp_id])

    def _run_all_mcps(self):
        """Run All MCPs sequentially with live dashboard, log, and intel updates.
        Completion-driven (not timer-based) for safety and correctness."""
        if self._batch_running:
            self.log_message("Run All already in progress.")
            return
        if self._workflow_running:
            self.log_message("Cannot start Run All while Workflow is active. Stop first.")
            return

        self._batch_running = True
        self._batch_queue = list(self.mcp_tab_widgets.keys())
        self.run_all_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
        self.log_message("=== Starting Run All MCPs (sequential) ===")
        self._update_status("Run All in progress...")
        self._advance_batch()

    def _advance_batch(self):
        """Start the next MCP in the batch queue. Triggered on previous completion."""
        if not self._batch_running or not self._batch_queue:
            self._finish_batch()
            return

        mcp_id = self._batch_queue.pop(0)
        tab = self.mcp_tab_widgets.get(mcp_id)
        if tab:
            self.log_message(f"Batch: launching {mcp_id} ({len(self._batch_queue) + 1} remaining)")
            # Tab.execute() will report 'Running' status which updates card + enables Stop
            tab.execute()
        else:
            # Skip bad entry and continue
            QTimer.singleShot(50, self._advance_batch)

    def _finish_batch(self):
        """Called when Run All queue is exhausted or aborted."""
        self._batch_running = False
        self._batch_queue = []
        self.log_message("=== Run All MCPs complete ===")
        self.update_intel("[BATCH] Run All finished. Check intel and exports for details.")
        self.run_all_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(False)
        self._update_status("Run All complete")
        self._refresh_stop_button()

    def _stop_all(self):
        """Stop all running MCP processes. Aborts any batch Run All or workflow."""
        stopped = 0

        # Abort batch Run All
        if self._batch_running:
            self._batch_running = False
            self._batch_queue = []

        # Abort workflow
        if self._workflow_running:
            self._workflow_running = False
            self._workflow_queue = []
            self._current_workflow_step = None
            if hasattr(self, 'exec_workflow_btn'):
                self.exec_workflow_btn.setEnabled(True)

        for mcp_id, tab in self.mcp_tab_widgets.items():
            if hasattr(tab, 'stop') and hasattr(tab, 'process') and tab.process and tab.process.state() != QProcess.NotRunning:
                tab.stop()
                stopped += 1

        self.running_processes.clear()
        self.log_message(f"Stop All: terminated {stopped} process(es).")
        self.run_all_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(False)
        self._update_status("All processes stopped")
        self._refresh_stop_button()

    def _refresh_stop_button(self):
        """Enable global Stop All only when at least one MCP process is actually running."""
        any_running = False
        for tab in getattr(self, 'mcp_tab_widgets', {}).values():
            if hasattr(tab, 'process') and tab.process is not None and tab.process.state() != QProcess.NotRunning:
                any_running = True
                break
        if hasattr(self, 'stop_all_btn'):
            self.stop_all_btn.setEnabled(any_running)

    # Workflow builder
    def _add_to_workflow(self):
        mcp_id = self.add_mcp_combo.currentData()
        if mcp_id and mcp_id not in self.workflow_chain:
            self.workflow_chain.append(mcp_id)
            self._refresh_workflow_list()

    def _refresh_workflow_list(self):
        self.workflow_list.clear()
        for mid in self.workflow_chain:
            mcp = get_mcp_by_id(mid)
            if mcp:
                prefix = "▶ " if self._current_workflow_step == mid else "  "
                item_text = f"{prefix}{mcp['name']}"
                if self._workflow_running and self._current_workflow_step == mid:
                    item_text += "  [RUNNING]"
                self.workflow_list.addItem(item_text)

    def _move_workflow_up(self):
        idx = self.workflow_list.currentRow()
        if idx > 0:
            self.workflow_chain[idx], self.workflow_chain[idx-1] = self.workflow_chain[idx-1], self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _move_workflow_down(self):
        idx = self.workflow_list.currentRow()
        if idx < len(self.workflow_chain) - 1:
            self.workflow_chain[idx], self.workflow_chain[idx+1] = self.workflow_chain[idx+1], self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _remove_from_workflow(self):
        idx = self.workflow_list.currentRow()
        if idx >= 0:
            del self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _execute_workflow(self):
        """Execute the user-defined workflow chain sequentially with live status."""
        if self._workflow_running:
            self.log_message("Workflow already running.")
            return
        if self._batch_running:
            self.log_message("Cannot start workflow while Run All is active. Stop first.")
            return
        if not self.workflow_chain:
            self.log_message("Workflow chain is empty.")
            return

        self._workflow_running = True
        self._workflow_queue = self.workflow_chain[:]
        self.exec_workflow_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
        self.log_message("=== Starting Workflow Chain ===")
        self._update_status("Workflow executing...")
        self._advance_workflow()

    def _advance_workflow(self):
        """Start next step in workflow. Called on previous step completion."""
        if not self._workflow_running or not self._workflow_queue:
            self._finish_workflow()
            return

        mcp_id = self._workflow_queue.pop(0)
        self._current_workflow_step = mcp_id
        self._refresh_workflow_list()
        tab = self.mcp_tab_widgets.get(mcp_id)
        if tab:
            self.log_message(f"Workflow step: {get_mcp_by_id(mcp_id)['name']} ({len(self._workflow_queue) + 1} remaining)")
            tab.execute()  # Tab will report Running status -> live card
        else:
            QTimer.singleShot(50, self._advance_workflow)

    def _finish_workflow(self):
        """Workflow finished or aborted."""
        self._workflow_running = False
        self._workflow_queue = []
        self._current_workflow_step = None
        self.log_message("=== Workflow Chain complete ===")
        self.update_intel("[WORKFLOW] Chain finished. Results aggregated above.")
        if hasattr(self, 'exec_workflow_btn'):
            self.exec_workflow_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(False)
        self._update_status("Workflow complete")
        self._refresh_workflow_list()
        self._refresh_stop_button()

    def _clear_workflow(self):
        if self._workflow_running:
            self.log_message("Clear ignored while workflow running. Use Stop All.")
            return
        self.workflow_chain.clear()
        self._current_workflow_step = None
        self._refresh_workflow_list()

    def _on_global_target_changed(self, text):
        self.global_target = text.strip()
        for tab in self.mcp_tab_widgets.values():
            tab.sync_global_target(self.global_target)
        if hasattr(self, 'intel_edit') and self.intel_edit:
            self.intel_edit.append(f"[GLOBAL] Target: {self.global_target}")

    def update_mcp_status(self, mcp_id, status, progress=0, result=None):
        """Primary callback from MCPTab (and future batch/workflow) for live dashboard updates."""
        if mcp_id in self.dashboard_cards:
            self.dashboard_cards[mcp_id].update_status(status, progress)

        if status == "Running":
            self.status_bar.showMessage(f"Running {mcp_id}...")
            if hasattr(self, 'stop_all_btn'):
                self.stop_all_btn.setEnabled(True)
        elif status == "Stopped":
            self.status_bar.showMessage(f"Stopped {mcp_id}")
            self.log_message(f"MCP {mcp_id} stopped by user")
            if hasattr(self, 'intel_edit'):
                self.intel_edit.append(f"[{mcp_id}] Stopped")
            self._refresh_stop_button()
            # Drive Run All or Workflow on terminal status
            if self._batch_running and self._batch_queue:
                QTimer.singleShot(120, self._advance_batch)
            elif self._workflow_running and self._workflow_queue:
                QTimer.singleShot(120, self._advance_workflow)
        elif status in ("Success", "Failed"):
            msg = f"MCP {mcp_id} → {status}"
            if result:
                msg += f" | {result}"
            self.log_message(msg)
            if hasattr(self, 'intel_edit'):
                self.intel_edit.append(f"[{mcp_id}] {status}" + (f": {result}" if result else ""))
            self._refresh_stop_button()
            # Drive sequential Run All or Workflow forward on actual completion
            if self._batch_running and self._batch_queue:
                QTimer.singleShot(120, self._advance_batch)
            elif self._workflow_running and self._workflow_queue:
                QTimer.singleShot(120, self._advance_workflow)

    def update_intel(self, text):
        if hasattr(self, 'intel_edit'):
            self.intel_edit.append(text)

    def log_message(self, msg):
        if hasattr(self, 'universal_log'):
            self.universal_log.appendPlainText(msg)

    def _collect_evidence(self):
        text = self.universal_log.toPlainText()
        if text:
            path = write_watermarked_report(text, self.watermark_enabled, prefix="evidence")
            self.log_message(f"Evidence saved to {path}")

    def _update_status(self, msg):
        """Helper for status bar messages."""
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(msg)

    def _verify_and_install_kali_tools(self):
        """Check presence of key Kali tools using shutil.which. Reports to log and intel."""
        import shutil
        self.log_message("=== Verifying Kali tools (demo-safe check) ===")
        missing = []
        found = []
        for mcp in MCPS:
            pkgs = mcp.get("kali_packages", [])
            for pkg in pkgs:
                if pkg and shutil.which(pkg) or shutil.which(pkg + ".exe"):
                    found.append(pkg)
                else:
                    if pkg not in missing:
                        missing.append(pkg)
        if found:
            self.log_message(f"Found: {', '.join(sorted(set(found)))}")
            self.update_intel(f"[TOOLS] Present: {len(set(found))} tools")
        if missing:
            self.log_message(f"Missing (demo mode will simulate): {', '.join(missing[:10])}")
            self.update_intel(f"[TOOLS] Missing on this host: {len(missing)} (using demo outputs)")
        else:
            self.log_message("All referenced tools appear available.")
        self._update_status(f"Tool check complete: {len(set(found))} found, {len(missing)} simulated")

    def _switch_to_masterblaster_bridge(self):
        self.main_tabs.setCurrentWidget(self.mb_bridge)

    # Export and settings (usable product features)
    def _export_all_reports(self):
        """Export combined intel + universal log + recent MCP outputs to watermarked report."""
        content = []
        content.append("# MasterBlaster-Control Full Export")
        content.append(f"Generated: {__import__('datetime').datetime.now().isoformat()}")
        content.append(f"Global Target: {self.global_target or 'N/A'}")
        content.append("\n## Target Intel\n")
        content.append(self.intel_edit.toPlainText() or "(no intel yet)")
        content.append("\n## Universal Log\n")
        content.append(self.universal_log.toPlainText() or "(no log yet)")

        # Add per-MCP last results if we had storage (basic for now)
        content.append("\n## MCP Execution Summary\n")
        for mid, tab in self.mcp_tab_widgets.items():
            out = tab.output.toPlainText()[-1500:] if hasattr(tab, 'output') else ""
            if out:
                content.append(f"\n=== {mid} ===\n{out[:800]}...\n")

        full = "\n".join(content)
        path = write_watermarked_report(full, self.watermark_enabled, prefix="full_export")
        self.log_message(f"Full export saved to {path}")
        QMessageBox.information(self, "Export", f"Report exported:\n{path}")

    def _open_settings(self):
        """Simple settings dialog stub turned usable (watermark toggle + info)."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("MasterBlaster-Control Settings"))

        wm_cb = QCheckBox("Enable watermarks on reports")
        wm_cb.setChecked(self.watermark_enabled)
        wm_cb.toggled.connect(lambda v: setattr(self, 'watermark_enabled', v))
        lay.addWidget(wm_cb)

        lay.addWidget(QLabel("Watermark setting persists across runs."))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        lay.addWidget(close_btn)
        dlg.exec()
        self.settings.setValue("watermark", self.watermark_enabled)
        self.log_message("Settings updated.")

    def _show_about(self):
        QMessageBox.information(self, "About", 
            "MasterBlaster-Control v1.1\n\n"
            "Kali MCP Orchestration Control Plane\n"
            "• Live dashboard with real-time status\n"
            "• Sequential Run All + Stop All\n"
            "• Custom Workflow chains\n"
            "• Demo-safe execution (simulated when tools missing)\n"
            "• Exports and evidence collection\n\n"
            "For authorized security testing only.")

    def closeEvent(self, event):
        self.settings.sync()
        # Best effort stop on close
        try:
            self._stop_all()
        except Exception:
            pass
        super().closeEvent(event)
