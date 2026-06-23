from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .masterblaster_bridge import MasterBlasterBridge
from .mcp_definitions import MCPS, get_mcp_by_id
from .mcp_tab import MCPTab
from .p0_storage import P0Storage, StorageSnapshot
from .runner_simulator import MANIFESTS, RunnerSimulator
from .utils import dark_kali_stylesheet, write_watermarked_report


class DashboardCard(QFrame):
    def __init__(self, mcp_id, name, on_click=None, parent=None):
        super().__init__(parent)
        self.mcp_id = mcp_id
        self.name = name
        self.on_click = on_click

        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QFrame { background: #2a2a2a; border: 1px solid #444; border-radius: 6px; }")
        lay = QVBoxLayout(self)

        self.title = QLabel(f"<b>{name}</b>")
        lay.addWidget(self.title)

        self.status_label = QLabel("Idle")
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
        color = {
            "Idle": "#888",
            "Running": "#ffaa00",
            "Success": "#00ff9d",
            "Denied": "#ff4444",
            "Failed": "#ff4444",
            "Stopped": "#ff8800",
        }.get(status, "#888")
        border = "2px" if status in {"Running", "Stopped"} else "1px"
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color};")
        self.progress_bar.setValue(progress)
        self.setStyleSheet(
            f"QFrame {{ background: #2a2a2a; border: {border} solid {color}; border-radius: 6px; }}"
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MasterBlaster P0 Authorized Assessment Simulator")
        self.resize(1250, 820)

        self.settings = QSettings("MasterBlaster", "P0Simulator")
        self.global_target = ""
        self.watermark_enabled = self.settings.value("watermark", True, type=bool)
        self.ethics_accepted = self.settings.value("ethics_accepted", False, type=bool)
        self.runner = RunnerSimulator()
        self.storage = P0Storage.default()
        self.storage.initialize()

        self.dashboard_cards = {}
        self.workflow_chain = []
        self._batch_running = False
        self._batch_queue = []
        self._workflow_running = False
        self._workflow_queue = []
        self._current_workflow_step = None

        self._init_ui()
        self._apply_dark_theme()
        self._check_ethics()
        self._update_status("Ready - P0 simulator, no live target execution")

    def _init_ui(self):
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)

        logo = QLabel("MasterBlaster P0 Simulator")
        logo.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        logo.setStyleSheet("color: #00ff9d;")
        top_layout.addWidget(logo)

        badge = QLabel("DENY BY DEFAULT")
        badge.setStyleSheet("background: #ff4444; color: white; padding: 2px 8px; border-radius: 3px;")
        top_layout.addWidget(badge)

        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Authorized target binding, for example example.com")
        self.target_edit.setMinimumWidth(300)
        self.target_edit.textChanged.connect(self._on_global_target_changed)
        top_layout.addWidget(self.target_edit, 4)

        self.validate_btn = QPushButton("Validate Manifests")
        self.validate_btn.clicked.connect(self._verify_and_install_kali_tools)
        top_layout.addWidget(self.validate_btn)

        self.run_all_btn = QPushButton("Run P0 Simulators")
        self.run_all_btn.clicked.connect(self._run_all_mcps)
        top_layout.addWidget(self.run_all_btn)

        self.stop_all_btn = QPushButton("Stop Queue")
        self.stop_all_btn.clicked.connect(self._stop_all)
        self.stop_all_btn.setEnabled(False)
        top_layout.addWidget(self.stop_all_btn)

        self.setMenuBar(QMenuBar())
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("Export Report Draft", self._export_all_reports)
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("Ethics", lambda: self._show_ethics_dialog(force=True))
        help_menu.addAction("About", self._show_about)

        central_splitter = QSplitter(Qt.Orientation.Horizontal)

        sidebar = QWidget()
        sidebar.setMinimumWidth(230)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(5, 5, 5, 5)

        mcp_label = QLabel(f"Reviewed Adapters ({len(MCPS)})")
        mcp_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        side_layout.addWidget(mcp_label)

        self.mcp_list = QListWidget()
        self.mcp_list.setMaximumWidth(220)
        self.mcp_list.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        for mcp in MCPS:
            item = QListWidgetItem(f"  {mcp['name']}")
            item.setData(Qt.ItemDataRole.UserRole, mcp["id"])
            self.mcp_list.addItem(item)
        self.mcp_list.currentItemChanged.connect(self._on_mcp_selected)
        side_layout.addWidget(self.mcp_list)

        self.guardrails_btn = QPushButton("P0 Guardrails")
        self.guardrails_btn.clicked.connect(self._switch_to_masterblaster_bridge)
        side_layout.addWidget(self.guardrails_btn)
        central_splitter.addWidget(sidebar)

        self.main_tabs = QTabWidget()
        self.dashboard = self._build_live_dashboard()
        self.main_tabs.addTab(self.dashboard, "Dashboard")

        self.mcp_tab_widgets = {}
        for mcp in MCPS:
            tab = MCPTab(mcp, self)
            self.mcp_tab_widgets[mcp["id"]] = tab
            self.main_tabs.addTab(tab, mcp["name"])

        self.mb_bridge = MasterBlasterBridge(self)
        self.main_tabs.addTab(self.mb_bridge, "Guardrails")

        central_splitter.addWidget(self.main_tabs)
        central_splitter.setStretchFactor(1, 4)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("Target Intel"))
        self.intel_edit = QTextEdit()
        self.intel_edit.setReadOnly(True)
        right_layout.addWidget(self.intel_edit)

        right_layout.addWidget(QLabel("Workflow Builder"))
        self.workflow_list = QListWidget()
        right_layout.addWidget(self.workflow_list)

        wf_btns = QHBoxLayout()
        self.add_mcp_combo = QComboBox()
        for mcp in MCPS:
            self.add_mcp_combo.addItem(mcp["name"], mcp["id"])
        wf_btns.addWidget(self.add_mcp_combo)
        self.add_to_chain_btn = QPushButton("Add")
        self.add_to_chain_btn.clicked.connect(self._add_to_workflow)
        wf_btns.addWidget(self.add_to_chain_btn)
        right_layout.addLayout(wf_btns)

        chain_btns = QHBoxLayout()
        self.up_btn = QPushButton("Up")
        self.up_btn.clicked.connect(self._move_workflow_up)
        chain_btns.addWidget(self.up_btn)
        self.down_btn = QPushButton("Down")
        self.down_btn.clicked.connect(self._move_workflow_down)
        chain_btns.addWidget(self.down_btn)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._remove_from_workflow)
        chain_btns.addWidget(self.remove_btn)
        right_layout.addLayout(chain_btns)

        self.exec_workflow_btn = QPushButton("Execute Workflow")
        self.exec_workflow_btn.clicked.connect(self._execute_workflow)
        right_layout.addWidget(self.exec_workflow_btn)

        self.clear_chain_btn = QPushButton("Clear Chain")
        self.clear_chain_btn.clicked.connect(self._clear_workflow)
        right_layout.addWidget(self.clear_chain_btn)

        central_splitter.addWidget(right_panel)
        central_splitter.setSizes([240, 780, 300])

        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.addWidget(QLabel("Audit Log and Evidence Collector"))

        self.universal_log = QPlainTextEdit()
        self.universal_log.setReadOnly(True)
        self.universal_log.setMaximumHeight(110)
        bottom_layout.addWidget(self.universal_log)

        self.collect_btn = QPushButton("Collect Current Log as Evidence Draft")
        self.collect_btn.clicked.connect(self._collect_evidence)
        bottom_layout.addWidget(self.collect_btn)

        main_v = QVBoxLayout()
        main_v.addWidget(top_bar)
        main_v.addWidget(central_splitter, 1)
        main_v.addWidget(bottom_widget)

        central = QWidget()
        central.setLayout(main_v)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _apply_dark_theme(self):
        self.setStyleSheet(dark_kali_stylesheet())

    def _check_ethics(self):
        if not self.ethics_accepted:
            self._show_ethics_dialog()

    def _show_ethics_dialog(self, force=False):
        msg = QMessageBox(self)
        msg.setWindowTitle("Ethics and Authorization Notice")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(
            "MasterBlaster P0 is for explicitly authorized assessment planning and simulation only.\n\n"
            "P0 does not run live tools or access targets. Every simulator job is still target-bound, "
            "engagement-bound, expiring, signed, and policy-checked.\n\n"
            "Continue?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if msg.exec() == QMessageBox.StandardButton.Ok:
            self.ethics_accepted = True
            self.settings.setValue("ethics_accepted", True)
            return
        if force:
            QMessageBox.critical(self, "Access Denied", "Authorization notice was not accepted.")
        sys.exit(0)

    def _build_live_dashboard(self):
        container = QWidget()
        lay = QGridLayout(container)
        lay.setSpacing(8)
        for idx, mcp in enumerate(MCPS):
            card = DashboardCard(mcp["id"], mcp["name"], on_click=self._switch_to_mcp)
            self.dashboard_cards[mcp["id"]] = card
            lay.addWidget(card, idx // 2, idx % 2)
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        return scroll

    def _switch_to_mcp(self, mcp_id):
        if mcp_id in self.mcp_tab_widgets:
            self.main_tabs.setCurrentWidget(self.mcp_tab_widgets[mcp_id])

    def _on_mcp_selected(self, current, previous):
        if current:
            self._switch_to_mcp(current.data(Qt.ItemDataRole.UserRole))

    def _run_all_mcps(self):
        if self._batch_running:
            self.log_message("Run queue already in progress.")
            return
        if self._workflow_running:
            self.log_message("Cannot start run queue while workflow is active.")
            return
        self._batch_running = True
        self._batch_queue = list(self.mcp_tab_widgets.keys())
        self.run_all_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
        self.log_message("=== Starting P0 simulator queue ===")
        self._advance_batch()

    def _advance_batch(self):
        if not self._batch_running:
            return
        if not self._batch_queue:
            self._finish_batch()
            return
        mcp_id = self._batch_queue.pop(0)
        tab = self.mcp_tab_widgets.get(mcp_id)
        if tab:
            self.log_message(f"Queue launching {mcp_id}")
            tab.execute()
        else:
            QTimer.singleShot(50, self._advance_batch)

    def _finish_batch(self):
        self._batch_running = False
        self._batch_queue = []
        self.log_message("=== P0 simulator queue complete ===")
        self.update_intel("[QUEUE] All reviewed simulator adapters completed or denied.")
        self.run_all_btn.setEnabled(True)
        self._refresh_stop_button()
        self._update_status("P0 simulator queue complete")

    def _stop_all(self):
        stopped_batch = self._batch_running
        stopped_workflow = self._workflow_running
        self._batch_running = False
        self._batch_queue = []
        self._workflow_running = False
        self._workflow_queue = []
        self._current_workflow_step = None
        self.run_all_btn.setEnabled(True)
        self.exec_workflow_btn.setEnabled(True)
        self._refresh_workflow_list()
        self._refresh_stop_button()
        if stopped_batch or stopped_workflow:
            self.log_message("Queue stopped. No child processes were running.")
        self._update_status("Queue stopped")

    def _refresh_stop_button(self):
        self.stop_all_btn.setEnabled(self._batch_running or self._workflow_running)

    def _add_to_workflow(self):
        mcp_id = self.add_mcp_combo.currentData()
        if mcp_id:
            self.workflow_chain.append(mcp_id)
            self._refresh_workflow_list()

    def _refresh_workflow_list(self):
        self.workflow_list.clear()
        for mid in self.workflow_chain:
            mcp = get_mcp_by_id(mid)
            if mcp:
                prefix = "> " if self._current_workflow_step == mid else "  "
                suffix = " [RUNNING]" if self._workflow_running and self._current_workflow_step == mid else ""
                self.workflow_list.addItem(f"{prefix}{mcp['name']}{suffix}")

    def _move_workflow_up(self):
        idx = self.workflow_list.currentRow()
        if idx > 0:
            self.workflow_chain[idx], self.workflow_chain[idx - 1] = self.workflow_chain[idx - 1], self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _move_workflow_down(self):
        idx = self.workflow_list.currentRow()
        if 0 <= idx < len(self.workflow_chain) - 1:
            self.workflow_chain[idx], self.workflow_chain[idx + 1] = self.workflow_chain[idx + 1], self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _remove_from_workflow(self):
        idx = self.workflow_list.currentRow()
        if idx >= 0:
            del self.workflow_chain[idx]
            self._refresh_workflow_list()

    def _execute_workflow(self):
        if self._workflow_running:
            self.log_message("Workflow already running.")
            return
        if self._batch_running:
            self.log_message("Cannot start workflow while queue is active.")
            return
        if not self.workflow_chain:
            self.log_message("Workflow chain is empty.")
            return
        self._workflow_running = True
        self._workflow_queue = self.workflow_chain[:]
        self.exec_workflow_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
        self.log_message("=== Starting P0 workflow ===")
        self._advance_workflow()

    def _advance_workflow(self):
        if not self._workflow_running:
            return
        if not self._workflow_queue:
            self._finish_workflow()
            return
        mcp_id = self._workflow_queue.pop(0)
        self._current_workflow_step = mcp_id
        self._refresh_workflow_list()
        tab = self.mcp_tab_widgets.get(mcp_id)
        if tab:
            self.log_message(f"Workflow launching {mcp_id}")
            tab.execute()
        else:
            QTimer.singleShot(50, self._advance_workflow)

    def _finish_workflow(self):
        self._workflow_running = False
        self._workflow_queue = []
        self._current_workflow_step = None
        self.exec_workflow_btn.setEnabled(True)
        self.log_message("=== P0 workflow complete ===")
        self.update_intel("[WORKFLOW] Reviewed simulator workflow finished.")
        self._refresh_workflow_list()
        self._refresh_stop_button()
        self._update_status("P0 workflow complete")

    def _clear_workflow(self):
        if self._workflow_running:
            self.log_message("Clear ignored while workflow is running. Stop queue first.")
            return
        self.workflow_chain.clear()
        self._current_workflow_step = None
        self._refresh_workflow_list()

    def _on_global_target_changed(self, text):
        self.global_target = text.strip()
        for tab in self.mcp_tab_widgets.values():
            tab.sync_global_target(self.global_target)
        if self.global_target:
            self.intel_edit.append(f"[GLOBAL] Target binding: {self.global_target}")

    def update_mcp_status(self, mcp_id, status, progress=0, result=None):
        if mcp_id in self.dashboard_cards:
            self.dashboard_cards[mcp_id].update_status(status, progress)
        if status == "Running":
            self._update_status(f"Running simulator {mcp_id}")
            return
        if status not in {"Success", "Denied", "Failed", "Stopped"}:
            return

        message = f"Simulator {mcp_id} -> {status}"
        if result:
            message += f" ({result})"
        self.log_message(message)
        self.intel_edit.append(f"[{mcp_id}] {status}" + (f": {result}" if result else ""))

        if self._batch_running:
            callback = self._advance_batch if self._batch_queue else self._finish_batch
            QTimer.singleShot(100, callback)
        elif self._workflow_running:
            callback = self._advance_workflow if self._workflow_queue else self._finish_workflow
            QTimer.singleShot(100, callback)
        self._refresh_stop_button()

    def update_intel(self, text):
        self.intel_edit.append(text)

    def record_runner_result(self, result) -> StorageSnapshot:
        self.storage.record_runner_result(result)
        snapshot = self.storage.snapshot()
        self.log_message(
            "Storage snapshot: "
            f"{snapshot.jobs} job(s), {snapshot.evidence_records} evidence record(s), "
            f"{snapshot.audit_events} audit event(s)"
        )
        return snapshot

    def log_message(self, msg):
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.universal_log.appendPlainText(f"{timestamp} {msg}")

    def _collect_evidence(self):
        text = self.universal_log.toPlainText()
        if text:
            path = write_watermarked_report(text, self.watermark_enabled, prefix="evidence_draft")
            self.log_message(f"Evidence draft saved to {path}")

    def _update_status(self, msg):
        self.status_bar.showMessage(msg)

    def _verify_and_install_kali_tools(self):
        self.log_message("=== Validating reviewed P0 manifests ===")
        for manifest in MANIFESTS.values():
            transport = "network" if manifest.network_access else "no-network"
            state = "reviewed" if manifest.reviewed else "unreviewed"
            self.log_message(f"{manifest.adapter_id} {manifest.version}: {state}, {transport}, {manifest.execution_mode}")
        self.update_intel(f"[MANIFESTS] {len(MANIFESTS)} reviewed adapter manifest(s) loaded.")
        self._update_status("Manifest validation complete")

    def _switch_to_masterblaster_bridge(self):
        self.main_tabs.setCurrentWidget(self.mb_bridge)

    def _export_all_reports(self):
        content = [
            "# MasterBlaster P0 Report Draft",
            f"Generated: {datetime.now().isoformat()}",
            f"Global target binding: {self.global_target or 'N/A'}",
            "",
            "## Target Intel",
            self.intel_edit.toPlainText() or "(no intel yet)",
            "",
            "## Audit Log",
            self.universal_log.toPlainText() or "(no log yet)",
            "",
            "## Storage Snapshot",
            self._storage_snapshot_text(),
            "",
            "## Latest Persistent Audit Events",
            self._persistent_audit_text(),
            "",
            "## Latest Persistent Evidence",
            self._persistent_evidence_text(),
            "",
            "## Adapter Outputs",
        ]
        for mid, tab in self.mcp_tab_widgets.items():
            out = tab.output.toPlainText()
            if out:
                content.append(f"\n### {mid}\n{out[-2000:]}")
        path = write_watermarked_report("\n".join(content), self.watermark_enabled, prefix="report_draft")
        self.log_message(f"Report draft saved to {path}")
        QMessageBox.information(self, "Export", f"Report draft exported:\n{path}")

    def _open_settings(self):
        from PySide6.QtWidgets import QDialog

        dlg = QDialog(self)
        dlg.setWindowTitle("Settings")
        lay = QVBoxLayout(dlg)
        wm_cb = QCheckBox("Enable watermarks on report drafts")
        wm_cb.setChecked(self.watermark_enabled)
        wm_cb.toggled.connect(lambda value: setattr(self, "watermark_enabled", value))
        lay.addWidget(wm_cb)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        lay.addWidget(close_btn)
        dlg.exec()
        self.settings.setValue("watermark", self.watermark_enabled)
        self.log_message("Settings updated.")

    def _show_about(self):
        QMessageBox.information(
            self,
            "About",
            "MasterBlaster P0 Authorized Assessment Simulator\n\n"
            "No live tools are executed. Jobs are manifest-bound, scope-checked, signed, "
            "expiring, and validated by the runner simulator before fixture evidence is emitted.",
        )

    def _storage_snapshot_text(self):
        snapshot = self.storage.snapshot()
        return (
            f"Tenants: {snapshot.tenants}\n"
            f"Clients: {snapshot.clients}\n"
            f"Engagements: {snapshot.engagements}\n"
            f"Jobs: {snapshot.jobs}\n"
            f"Evidence records: {snapshot.evidence_records}\n"
            f"Audit events: {snapshot.audit_events}"
        )

    def _persistent_audit_text(self):
        events = self.storage.list_audit_events(limit=10)
        if not events:
            return "(no persistent audit events yet)"
        return "\n".join(
            f"- {event['created_at']} {event['action']} {event['reason_code']} {event['details']}"
            for event in events
        )

    def _persistent_evidence_text(self):
        records = self.storage.list_evidence(limit=10)
        if not records:
            return "(no persistent evidence yet)"
        return "\n".join(
            f"- {record['evidence_id']} job={record['job_id']} sha256={record['sha256']}"
            for record in records
        )

    def closeEvent(self, event):
        self.settings.sync()
        self._stop_all()
        self.storage.close()
        super().closeEvent(event)
