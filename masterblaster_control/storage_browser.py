from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .p0_storage import P0Storage


class StorageBrowser(QWidget):
    """Read-only browser for persisted tenants, engagements, audit events, and evidence."""

    def __init__(self, storage: P0Storage, parent=None):
        super().__init__(parent)
        self.storage = storage
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel("Local simulator records (read-only)"))
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.tabs = QTabWidget()

        self.engagement_table = self._make_table(
            ["Engagement", "Tenant", "Client", "Scope", "Expires", "Updated"]
        )
        self.tabs.addTab(self.engagement_table, "Engagements")

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

        self.evidence_table = self._make_table(
            ["Evidence ID", "Job", "Adapter", "Target", "Parser", "SHA-256"]
        )
        evidence_tab = QWidget()
        evidence_layout = QVBoxLayout(evidence_tab)
        evidence_filters = QHBoxLayout()
        evidence_filters.addWidget(QLabel("Adapter"))
        self.evidence_adapter_filter = QComboBox()
        self.evidence_adapter_filter.addItem("All adapters", "")
        self.evidence_adapter_filter.currentIndexChanged.connect(self._refresh_evidence_table)
        evidence_filters.addWidget(self.evidence_adapter_filter)
        evidence_filters.addWidget(QLabel("Search"))
        self.evidence_search = QLineEdit()
        self.evidence_search.setPlaceholderText("Filter target or hash")
        self.evidence_search.textChanged.connect(self._refresh_evidence_table)
        evidence_filters.addWidget(self.evidence_search, 1)
        evidence_layout.addLayout(evidence_filters)
        evidence_layout.addWidget(self.evidence_table)
        self.tabs.addTab(evidence_tab, "Evidence")

        layout.addWidget(self.tabs)

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
        events = self.storage.list_audit_events(
            limit=200,
            action=self.audit_action_filter.currentData() or None,
            reason_code=self.audit_reason_filter.currentData() or None,
            search=self.audit_search.text().strip() or None,
        )
        self.audit_table.setRowCount(len(events))
        for row_idx, event in enumerate(events):
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
                self.audit_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def _refresh_evidence_table(self) -> None:
        records = self.storage.list_evidence(
            limit=200,
            adapter_id=self.evidence_adapter_filter.currentData() or None,
            search=self.evidence_search.text().strip() or None,
        )
        self.evidence_table.setRowCount(len(records))
        for row_idx, record in enumerate(records):
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