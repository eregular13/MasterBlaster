from __future__ import annotations

import json

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from .p0_resources import list_resources, read_resource, resource_summary_markdown
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

        buttons = QHBoxLayout()

        self.refresh_btn = QPushButton("List Reviewed Adapter Manifests")
        self.refresh_btn.clicked.connect(self.refresh_scripts)
        buttons.addWidget(self.refresh_btn)

        self.resources_btn = QPushButton("List Non-Executing Resources")
        self.resources_btn.clicked.connect(self.refresh_resources)
        buttons.addWidget(self.resources_btn)

        self.checklist_btn = QPushButton("Show P0 Checklist")
        self.checklist_btn.clicked.connect(self.show_acceptance_checklist)
        buttons.addWidget(self.checklist_btn)

        lay.addLayout(buttons)

        self.refresh_scripts()

    def refresh_scripts(self):
        self.output.clear()
        payload = [manifest.to_mcp_definition() for manifest in MANIFESTS.values()]
        self.output.append(json.dumps(payload, indent=2, sort_keys=True))

    def refresh_resources(self):
        self.output.clear()
        payload = [resource.to_dict() for resource in list_resources()]
        self.output.append(json.dumps(payload, indent=2, sort_keys=True))
        self.output.append("\n" + resource_summary_markdown())

    def show_acceptance_checklist(self):
        self.output.clear()
        self.output.append(read_resource("p0://governance/acceptance-checklist").body)

    def _launch_selected(self):
        self.output.append("Denied: P0 does not allow direct script execution.")
