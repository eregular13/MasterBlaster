"""Firm branding and configuration — logo upload, signatories, billing defaults."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .business_config import FirmConfig, load_firm_config, save_firm_config
from .live_tool_runbook import export_runbook_markdown
from .utils import write_export_file


LOGO_DIR = Path("data") / "business" / "assets"


class FirmSettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "<b>Firm Settings</b><br>"
                "Configure branding for client deliverables — company name, logo, signatories, and billing defaults."
            )
        )

        form = QFormLayout()
        self.firm_name = QLineEdit()
        form.addRow("Firm name:", self.firm_name)

        self.tagline = QLineEdit()
        form.addRow("Tagline:", self.tagline)

        self.watermark = QLineEdit()
        form.addRow("Report watermark:", self.watermark)

        self.hourly_rate = QLineEdit()
        form.addRow("Default hourly rate (USD):", self.hourly_rate)

        self.lead_assessor = QLineEdit()
        form.addRow("Lead assessor name:", self.lead_assessor)

        self.lead_title = QLineEdit()
        form.addRow("Lead assessor title:", self.lead_title)

        self.client_approver = QLineEdit()
        form.addRow("Client approver label:", self.client_approver)

        self.logo_path_label = QLabel("No logo configured")
        logo_row = QHBoxLayout()
        logo_row.addWidget(self.logo_path_label, 1)
        upload_btn = QPushButton("Upload Logo (PNG/JPG)")
        upload_btn.clicked.connect(self._upload_logo)
        logo_row.addWidget(upload_btn)
        form.addRow("Logo:", logo_row)

        root.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        buttons.addWidget(save_btn)

        runbook_btn = QPushButton("Export Live Transport Runbook")
        runbook_btn.clicked.connect(self._export_runbook)
        buttons.addWidget(runbook_btn)
        root.addLayout(buttons)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        root.addWidget(self.output, 1)

    def _load_config(self):
        cfg = load_firm_config()
        self.firm_name.setText(cfg.firm_name)
        self.tagline.setText(cfg.tagline)
        self.watermark.setText(cfg.report_watermark)
        self.hourly_rate.setText(str(cfg.default_hourly_rate_usd))
        self.lead_assessor.setText(cfg.lead_assessor_name)
        self.lead_title.setText(cfg.lead_assessor_title)
        self.client_approver.setText(cfg.client_approver_label)
        if cfg.logo_path and Path(cfg.logo_path).exists():
            self.logo_path_label.setText(cfg.logo_path)
        self.output.setPlainText(f"Loaded firm config for: {cfg.firm_name}")

    def _upload_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select firm logo",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.webp)",
        )
        if not path:
            return
        LOGO_DIR.mkdir(parents=True, exist_ok=True)
        dest = LOGO_DIR / Path(path).name
        shutil.copy2(path, dest)
        cfg = load_firm_config()
        cfg.logo_path = str(dest)
        save_firm_config(cfg)
        self.logo_path_label.setText(str(dest))
        self.main.log_message(f"Logo uploaded: {dest}")
        QMessageBox.information(self, "Logo", f"Logo saved and linked:\n{dest}")

    def _save_settings(self):
        try:
            rate = float(self.hourly_rate.text().strip() or "225")
        except ValueError:
            QMessageBox.warning(self, "Validation", "Hourly rate must be numeric.")
            return
        cfg = FirmConfig(
            firm_name=self.firm_name.text().strip() or "Your Security Firm",
            tagline=self.tagline.text().strip(),
            report_watermark=self.watermark.text().strip(),
            default_hourly_rate_usd=rate,
            lead_assessor_name=self.lead_assessor.text().strip(),
            lead_assessor_title=self.lead_title.text().strip(),
            client_approver_label=self.client_approver.text().strip(),
            logo_path=self.logo_path_label.text() if "No logo" not in self.logo_path_label.text() else "",
        )
        save_firm_config(cfg)
        self.output.setPlainText(f"Settings saved for {cfg.firm_name}")
        self.main.log_message("Firm settings saved")
        QMessageBox.information(self, "Settings", "Firm configuration saved.")

    def _export_runbook(self):
        path = write_export_file(export_runbook_markdown(), "live_transport_runbook", "md")
        self.output.setPlainText(export_runbook_markdown())
        self.main.log_message(f"Runbook exported: {path}")
        QMessageBox.information(self, "Runbook", f"Live transport runbook saved:\n{path}")