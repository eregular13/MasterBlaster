from __future__ import annotations

import json

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from .engagement_picker import resolve_engagement
from .p0_acceptance import acceptance_dashboard_markdown
from .p0_resources import list_resources, read_resource, resource_summary_markdown
from .p7_plugins import discover_plugins, plugin_catalog_markdown, reload_plugins, set_plugin_dev_mode
from .p7_workflow_generator import generate_workflow_draft, workflow_draft_markdown
from .p8_workflow_assistant import assistant_markdown
from .phase_tracker import phases_dashboard_markdown
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

        self.dashboard_btn = QPushButton("Show Acceptance Dashboard")
        self.dashboard_btn.clicked.connect(self.show_acceptance_dashboard)
        buttons.addWidget(self.dashboard_btn)

        row2 = QHBoxLayout()
        self.phase_btn = QPushButton("Phase Roadmap P0-P8")
        self.phase_btn.clicked.connect(self.show_phase_roadmap)
        row2.addWidget(self.phase_btn)

        self.plugins_btn = QPushButton("Plugin Catalog")
        self.plugins_btn.clicked.connect(self.show_plugin_catalog)
        row2.addWidget(self.plugins_btn)

        self.workflow_btn = QPushButton("Generate Workflow Draft")
        self.workflow_btn.setToolTip("Build a non-executing workflow draft for the active engagement.")
        self.workflow_btn.clicked.connect(self.show_workflow_draft)
        row2.addWidget(self.workflow_btn)

        self.assistant_btn = QPushButton("Enrich with Assistant")
        self.assistant_btn.setToolTip("Add deterministic planning suggestions — no LLM, no execution.")
        self.assistant_btn.clicked.connect(self.show_assistant_enrichment)
        row2.addWidget(self.assistant_btn)

        row3 = QHBoxLayout()
        self.hot_reload_btn = QPushButton("Hot-Reload Plugins")
        self.hot_reload_btn.setToolTip("Re-scan plugin manifests from disk (dev mode).")
        self.hot_reload_btn.clicked.connect(self.hot_reload_plugins)
        row3.addWidget(self.hot_reload_btn)

        lay.addLayout(buttons)
        lay.addLayout(row2)
        lay.addLayout(row3)

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

    def show_acceptance_dashboard(self):
        self.output.clear()
        self.output.append(acceptance_dashboard_markdown())

    def show_phase_roadmap(self):
        self.output.clear()
        self.output.append(phases_dashboard_markdown())

    def show_plugin_catalog(self):
        self.output.clear()
        plugins = discover_plugins()
        self.output.append(plugin_catalog_markdown(plugins))
        self.output.append(json.dumps([plugin.to_dict() for plugin in plugins], indent=2, sort_keys=True))

    def show_workflow_draft(self):
        self.output.clear()
        target = getattr(self.main, "global_target", "") or "example.com"
        engagement = resolve_engagement(self.main.storage, getattr(self.main, "selected_engagement_id", "") or None, target)
        draft = generate_workflow_draft(engagement)
        self.output.append(workflow_draft_markdown(draft))

    def show_assistant_enrichment(self):
        self.output.clear()
        target = getattr(self.main, "global_target", "") or "example.com"
        engagement = resolve_engagement(self.main.storage, getattr(self.main, "selected_engagement_id", "") or None, target)
        draft = generate_workflow_draft(engagement)
        self.output.append(assistant_markdown(draft))

    def hot_reload_plugins(self):
        set_plugin_dev_mode(True)
        plugins = reload_plugins()
        self.output.clear()
        self.output.append(f"Hot-reloaded {len(plugins)} plugin manifest(s).")
        self.output.append(plugin_catalog_markdown(plugins))

    def _launch_selected(self):
        self.output.append("Denied: P0 does not allow direct script execution.")
