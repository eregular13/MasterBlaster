from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .engagement_picker import update_engagement_scope
from .p0_models import Engagement, RulesOfEngagement, ScopeTarget
from .p0_storage import P0Storage
from .utils import write_export_file


class StorageBrowser(QWidget):
    """Browser and controlled create forms for local simulator records."""

    def __init__(self, storage: P0Storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._audit_events: list[dict] = []
        self._evidence_records: list[dict] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("Local simulator records"))
        self.export_audit_btn = QPushButton("Export Audit CSV")
        self.export_audit_btn.clicked.connect(self._export_audit_csv)
        header.addWidget(self.export_audit_btn)
        self.export_evidence_btn = QPushButton("Export Evidence JSON")
        self.export_evidence_btn.clicked.connect(self._export_evidence_json)
        header.addWidget(self.export_evidence_btn)
        self.copy_hash_btn = QPushButton("Copy SHA-256")
        self.copy_hash_btn.clicked.connect(self._copy_selected_hash)
        header.addWidget(self.copy_hash_btn)
        header.addStretch()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()

        manage_tab = QWidget()
        manage_layout = QVBoxLayout(manage_tab)

        tenant_box = QGroupBox("Create Tenant")
        tenant_form = QFormLayout(tenant_box)
        self.tenant_id_input = QLineEdit()
        self.tenant_name_input = QLineEdit()
        tenant_form.addRow("Tenant ID", self.tenant_id_input)
        tenant_form.addRow("Display Name", self.tenant_name_input)
        tenant_save = QPushButton("Save Tenant")
        tenant_save.clicked.connect(self._save_tenant)
        tenant_form.addRow(tenant_save)
        manage_layout.addWidget(tenant_box)

        client_box = QGroupBox("Create Client")
        client_form = QFormLayout(client_box)
        self.client_id_input = QLineEdit()
        self.client_tenant_input = QLineEdit()
        self.client_name_input = QLineEdit()
        client_form.addRow("Client ID", self.client_id_input)
        client_form.addRow("Tenant ID", self.client_tenant_input)
        client_form.addRow("Display Name", self.client_name_input)
        client_save = QPushButton("Save Client")
        client_save.clicked.connect(self._save_client)
        client_form.addRow(client_save)
        manage_layout.addWidget(client_box)

        engagement_box = QGroupBox("Create Engagement")
        engagement_form = QFormLayout(engagement_box)
        self.engagement_id_input = QLineEdit()
        self.engagement_tenant_input = QLineEdit()
        self.engagement_client_input = QLineEdit()
        self.engagement_scope_input = QLineEdit()
        self.engagement_scope_input.setPlaceholderText("example.com, 10.0.0.0/24")
        self.engagement_minutes_input = QSpinBox()
        self.engagement_minutes_input.setRange(5, 1440)
        self.engagement_minutes_input.setValue(60)
        engagement_form.addRow("Engagement ID", self.engagement_id_input)
        engagement_form.addRow("Tenant ID", self.engagement_tenant_input)
        engagement_form.addRow("Client ID", self.engagement_client_input)
        engagement_form.addRow("Authorized Scope", self.engagement_scope_input)
        engagement_form.addRow("Expires In (minutes)", self.engagement_minutes_input)
        engagement_save = QPushButton("Save Engagement")
        engagement_save.clicked.connect(self._save_engagement)
        engagement_form.addRow(engagement_save)
        manage_layout.addWidget(engagement_box)
        manage_layout.addStretch()
        self.tabs.addTab(manage_tab, "Manage")

        engagement_tab = QWidget()
        engagement_layout = QVBoxLayout(engagement_tab)
        self.engagement_table = self._make_table(
            ["Engagement", "Tenant", "Client", "Scope", "Expires", "Updated"]
        )
        engagement_layout.addWidget(self.engagement_table)
        engagement_actions = QHBoxLayout()
        self.edit_engagement_btn = QPushButton("Edit Selected Engagement")
        self.edit_engagement_btn.clicked.connect(self._edit_selected_engagement)
        engagement_actions.addWidget(self.edit_engagement_btn)
        self.delete_engagement_btn = QPushButton("Delete Selected Engagement")
        self.delete_engagement_btn.clicked.connect(self._delete_selected_engagement)
        engagement_actions.addWidget(self.delete_engagement_btn)
        engagement_actions.addStretch()
        engagement_layout.addLayout(engagement_actions)
        self.tabs.addTab(engagement_tab, "Engagements")

        self.audit_table = self._make_table(
            ["Time", "Action", "Reason", "Engagement", "Details"]
        )
        audit_tab = QWidget()
        audit_layout = QVBoxLayout(audit_tab)
        audit_filters = QHBoxLayout()
        audit_filters.addWidget(QLabel("Action"))
        self.audit_action_filter = QComboBox()
        self.audit_action_filter.addItem("All actions", "")
        self.audit_action_filter.currentIndexChanged.connect(self._refresh_audit_table)
        audit_filters.addWidget(self.audit_action_filter)
        audit_filters.addWidget(QLabel("Reason"))
        self.audit_reason_filter = QComboBox()
        self.audit_reason_filter.addItem("All reasons", "")
        self.audit_reason_filter.currentIndexChanged.connect(self._refresh_audit_table)
        audit_filters.addWidget(self.audit_reason_filter)
        audit_filters.addWidget(QLabel("Search"))
        self.audit_search = QLineEdit()
        self.audit_search.setPlaceholderText("Filter details text")
        self.audit_search.textChanged.connect(self._refresh_audit_table)
        audit_filters.addWidget(self.audit_search, 1)
        audit_layout.addLayout(audit_filters)
        audit_layout.addWidget(self.audit_table)
        self.tabs.addTab(audit_tab, "Audit Events")

        self.evidence_tab = QWidget()
        evidence_layout = QVBoxLayout(self.evidence_tab)
        evidence_filters = QHBoxLayout()
        evidence_filters.addWidget(QLabel("Adapter"))
        self.evidence_adapter_filter = QComboBox()
        self.evidence_adapter_filter.addItem("All adapters", "")
        self.evidence_adapter_filter.currentIndexChanged.connect(self._refresh_evidence_table)
        evidence_filters.addWidget(self.evidence_adapter_filter)
        evidence_filters.addWidget(QLabel("Search"))
        self.evidence_search = QLineEdit()
        self.evidence_search.setPlaceholderText("Filter target, hash, or job id")
        self.evidence_search.textChanged.connect(self._refresh_evidence_table)
        evidence_filters.addWidget(self.evidence_search, 1)
        evidence_layout.addLayout(evidence_filters)
        self.evidence_table = self._make_table(
            ["Evidence ID", "Job", "Adapter", "Target", "Parser", "SHA-256"]
        )
        evidence_layout.addWidget(self.evidence_table)
        evidence_layout.addWidget(QLabel("Evidence Detail"))
        self.evidence_detail = QPlainTextEdit()
        self.evidence_detail.setReadOnly(True)
        self.evidence_detail.setMaximumHeight(180)
        evidence_layout.addWidget(self.evidence_detail)
        self.tabs.addTab(self.evidence_tab, "Evidence")

        layout.addWidget(self.tabs)

        self.audit_table.doubleClicked.connect(self._deep_link_audit_to_evidence)
        self.evidence_table.itemSelectionChanged.connect(self._show_evidence_detail)

    def _make_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def refresh(self) -> None:
        self._refresh_engagement_table()
        self._refresh_audit_filters()
        self._refresh_evidence_filters()
        self._refresh_audit_table()
        self._refresh_evidence_table()

    def _notify_main_refresh(self) -> None:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "_refresh_engagement_picker"):
                parent._refresh_engagement_picker()
                return
            parent = parent.parent()

    def _save_tenant(self) -> None:
        try:
            self.storage.create_tenant(self.tenant_id_input.text(), self.tenant_name_input.text())
            self.refresh()
            self._notify_main_refresh()
            QMessageBox.information(self, "Tenant Saved", "Tenant record saved.")
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))

    def _save_client(self) -> None:
        try:
            self.storage.create_client(
                self.client_id_input.text(),
                self.client_tenant_input.text(),
                self.client_name_input.text(),
            )
            self.refresh()
            QMessageBox.information(self, "Client Saved", "Client record saved.")
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))

    def _save_engagement(self) -> None:
        engagement_id = self.engagement_id_input.text().strip()
        tenant_id = self.engagement_tenant_input.text().strip()
        client_id = self.engagement_client_input.text().strip()
        scope_raw = self.engagement_scope_input.text().strip()
        if not all([engagement_id, tenant_id, client_id, scope_raw]):
            QMessageBox.warning(self, "Validation Error", "All engagement fields are required.")
            return
        patterns = tuple(ScopeTarget(pattern=item.strip()) for item in scope_raw.split(",") if item.strip())
        if not patterns:
            QMessageBox.warning(self, "Validation Error", "At least one authorized target is required.")
            return
        now = datetime.now(timezone.utc)
        engagement = Engagement(
            engagement_id=engagement_id,
            tenant_id=tenant_id,
            client_id=client_id,
            authorized_targets=patterns,
            rules=RulesOfEngagement(allow_network_transport=False, max_runtime_seconds=30),
            expires_at=now + timedelta(minutes=self.engagement_minutes_input.value()),
        )
        try:
            self.storage.save_engagement(engagement)
            self.refresh()
            self._notify_main_refresh()
            QMessageBox.information(self, "Engagement Saved", "Engagement record saved.")
        except Exception as exc:
            QMessageBox.warning(self, "Save Failed", str(exc))

    def _selected_engagement_id(self) -> str | None:
        row = self.engagement_table.currentRow()
        if row < 0:
            return None
        item = self.engagement_table.item(row, 0)
        return item.text() if item else None

    def _edit_selected_engagement(self) -> None:
        engagement_id = self._selected_engagement_id()
        if not engagement_id:
            QMessageBox.information(self, "Edit Engagement", "Select an engagement row first.")
            return
        scope, ok = QInputDialog.getText(
            self,
            "Edit Engagement Scope",
            "Comma-separated authorized targets:",
        )
        if not ok:
            return
        patterns = [item.strip() for item in scope.split(",") if item.strip()]
        if not patterns:
            QMessageBox.warning(self, "Validation Error", "Scope cannot be empty.")
            return
        update_engagement_scope(self.storage, engagement_id, patterns, expires_minutes=120)
        self.refresh()
        self._notify_main_refresh()
        QMessageBox.information(self, "Engagement Updated", f"Updated {engagement_id}.")

    def _delete_selected_engagement(self) -> None:
        engagement_id = self._selected_engagement_id()
        if not engagement_id:
            QMessageBox.information(self, "Delete Engagement", "Select an engagement row first.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete Engagement",
            f"Delete engagement {engagement_id} and related simulator records?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        deleted = self.storage.delete_engagement(engagement_id)
        if deleted:
            self.refresh()
            self._notify_main_refresh()
            QMessageBox.information(self, "Deleted", f"Engagement {engagement_id} deleted.")
        else:
            QMessageBox.warning(self, "Not Found", f"Engagement {engagement_id} was not found.")

    def _refresh_engagement_table(self) -> None:
        rows = self.storage.list_engagements(limit=100)
        self.engagement_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            scope = ", ".join(row.get("scope", []))
            values = [
                row["engagement_id"],
                row["tenant_id"],
                row["client_id"],
                scope,
                row["expires_at"],
                row["updated_at"],
            ]
            for col_idx, value in enumerate(values):
                self.engagement_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def _refresh_audit_filters(self) -> None:
        events = self.storage.list_audit_events(limit=200)
        actions = sorted({event["action"] for event in events})
        reasons = sorted({event["reason_code"] for event in events})
        self._repopulate_filter(self.audit_action_filter, "All actions", actions)
        self._repopulate_filter(self.audit_reason_filter, "All reasons", reasons)

    def _refresh_evidence_filters(self) -> None:
        records = self.storage.list_evidence(limit=200)
        adapters = sorted({record["adapter_id"] for record in records})
        self._repopulate_filter(self.evidence_adapter_filter, "All adapters", adapters)

    def _repopulate_filter(self, combo: QComboBox, all_label: str, values: list[str]) -> None:
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label, "")
        for value in values:
            combo.addItem(value, value)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def _refresh_audit_table(self) -> None:
        self._audit_events = self.storage.list_audit_events(
            limit=200,
            action=self.audit_action_filter.currentData() or None,
            reason_code=self.audit_reason_filter.currentData() or None,
            search=self.audit_search.text().strip() or None,
        )
        self.audit_table.setRowCount(len(self._audit_events))
        for row_idx, event in enumerate(self._audit_events):
            details = event.get("details", {})
            detail_text = ", ".join(f"{key}={value}" for key, value in details.items())
            values = [
                event["created_at"],
                event["action"],
                event["reason_code"],
                event["engagement_id"],
                detail_text,
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col_idx == 0:
                    item.setData(256, event.get("details", {}).get("job_id"))
                self.audit_table.setItem(row_idx, col_idx, item)

    def _refresh_evidence_table(self) -> None:
        self._evidence_records = self.storage.list_evidence(
            limit=200,
            adapter_id=self.evidence_adapter_filter.currentData() or None,
            search=self.evidence_search.text().strip() or None,
        )
        self.evidence_table.setRowCount(len(self._evidence_records))
        for row_idx, record in enumerate(self._evidence_records):
            values = [
                record["evidence_id"],
                record["job_id"],
                record["adapter_id"],
                record["target"],
                record["parser_id"],
                record["sha256"],
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col_idx == 5:
                    item.setToolTip(str(value))
                self.evidence_table.setItem(row_idx, col_idx, item)
        self._show_evidence_detail()

    def _deep_link_audit_to_evidence(self) -> None:
        row = self.audit_table.currentRow()
        if row < 0 or row >= len(self._audit_events):
            return
        job_id = self._audit_events[row].get("details", {}).get("job_id")
        if not job_id:
            QMessageBox.information(self, "No Evidence Link", "This audit event has no linked job id.")
            return
        self.tabs.setCurrentWidget(self.evidence_tab)
        self.evidence_search.setText(str(job_id))
        self._refresh_evidence_table()

    def _show_evidence_detail(self) -> None:
        row = self.evidence_table.currentRow()
        if row < 0 or row >= len(self._evidence_records):
            self.evidence_detail.setPlainText("")
            return
        record = self._evidence_records[row]
        self.evidence_detail.setPlainText(
            json.dumps(record.get("content", {}), indent=2, sort_keys=True)
        )

    def _export_audit_csv(self) -> None:
        path = write_export_file(self.storage.export_audit_events_csv(), "audit_export", "csv")
        QMessageBox.information(self, "Export Complete", f"Audit CSV exported:\n{path}")

    def _export_evidence_json(self) -> None:
        path = write_export_file(self.storage.export_evidence_json(), "evidence_export", "json")
        QMessageBox.information(self, "Export Complete", f"Evidence JSON exported:\n{path}")

    def _copy_selected_hash(self) -> None:
        row = self.evidence_table.currentRow()
        if row < 0 or row >= len(self._evidence_records):
            QMessageBox.information(self, "Copy", "Select an evidence row first.")
            return
        sha256 = self._evidence_records[row]["sha256"]
        QGuiApplication.clipboard().setText(sha256)
        QMessageBox.information(self, "Copied", "SHA-256 hash copied to clipboard.")