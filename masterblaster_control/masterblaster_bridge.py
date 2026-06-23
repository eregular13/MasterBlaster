from __future__ import annotations

import json

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from .runner_simulator import MANIFESTS


class MasterBlasterBridge(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

        lay = QVBoxLayout(self)
        lay.addWidget(
            QLabel(
                "<b>P0 Guardrails</b><br>"
                "Direct script launching is disabled. Simulator jobs must pass reviewed "
                "adapter manifests, scope policy, signed envelopes, and runner validation."
            )
        )

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        lay.addWidget(self.output)

        self.refresh_btn = QPushButton("List Reviewed Adapter Manifests")
        self.refresh_btn.clicked.connect(self.refresh_scripts)
        lay.addWidget(self.refresh_btn)

        self.refresh_scripts()

    def refresh_scripts(self):
        self.output.clear()
        payload = [manifest.to_mcp_definition() for manifest in MANIFESTS.values()]
        self.output.append(json.dumps(payload, indent=2, sort_keys=True))

    def _launch_selected(self):
        self.output.append("Denied: P0 does not allow direct script execution.")
