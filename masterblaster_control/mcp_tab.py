from __future__ import annotations

import json

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .p0_approvals import request_approval


class MCPTab(QWidget):
    def __init__(self, mcp_def, main_window):
        super().__init__()
        self.mcp = mcp_def
        self.main = main_window
        self.process = None
        self.fields = {}
        self._build_ui()
        if hasattr(self.main, "update_mcp_status"):
            self.main.update_mcp_status(self.mcp["id"], "Idle", 0)

    def _build_ui(self):
        lay = QVBoxLayout(self)

        title = QLabel(
            f"<b>{self.mcp['name']}</b><br>"
            f"{self.mcp.get('description', '')}<br>"
            f"Tier: {self.mcp.get('tier')} | Mode: {self.mcp.get('execution_mode')}"
        )
        lay.addWidget(title)

        form = QFormLayout()
        for parameter in self.mcp.get("params", ["target"]):
            field = QLineEdit()
            if parameter == "target":
                field.setText(getattr(self.main, "global_target", ""))
            self.fields[parameter] = field
            form.addRow(parameter.capitalize() + ":", field)
        lay.addLayout(form)

        btn_layout = QHBoxLayout()
        self.exec_btn = QPushButton(f"Run Simulator: {self.mcp['name']}")
        self.exec_btn.clicked.connect(self.execute)
        btn_layout.addWidget(self.exec_btn)

        self.stop_btn = QPushButton("Stop Queue")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        lay.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        lay.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background: #0a0a0a; font-family: Consolas; color: #d8ffe8;")
        lay.addWidget(QLabel("Policy, Job, and Evidence Output:"))
        lay.addWidget(self.output)

        self.results_label = QLabel("No simulator job has been requested.")
        lay.addWidget(self.results_label)

    def sync_global_target(self, target):
        if "target" in self.fields:
            self.fields["target"].setText(target)

    def execute(self):
        target = self._target_from_ui()
        if not target:
            self._finish_denied("DENY_INVALID_TARGET", "No target provided.")
            return

        adapter_id = self.mcp["adapter_id"]
        arguments = {
            parameter: field.text().strip()
            for parameter, field in self.fields.items()
            if field.text().strip()
        }
        arguments.setdefault("target", target)

        self.output.append(f"> Requesting signed simulator job for {adapter_id}")
        self.output.append(f"> Target binding: {target}")
        self.progress.setValue(30)
        self.exec_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        if hasattr(self.main, "update_mcp_status"):
            self.main.update_mcp_status(adapter_id, "Running", 30)

        engagement = self.main.current_engagement_for_target(target)
        if engagement is None:
            self._finish_denied(
                "DENY_ENGAGEMENT_SELECTION_REQUIRED",
                "Select a persisted, unexpired engagement before requesting simulator execution.",
            )
            return
        approval_request = request_approval(engagement, adapter_id, target)
        approval = self.main.request_human_approval(approval_request)
        self.output.append(f"Approval state: {approval.state} ({approval.decision_reason or 'pending'})")

        result = self.main.runner.run(
            adapter_id,
            target,
            engagement=engagement,
            approval=approval,
            arguments=arguments,
        )
        try:
            storage_snapshot = self.main.record_runner_result(result)
        except Exception as exc:
            self._finish_denied("DENY_STORAGE_FAILURE", f"Runner result could not be persisted: {exc}")
            return

        decision = result.decision
        self.output.append(f"Policy decision: {decision.reason_code} - {decision.message}")
        self.output.append(
            "Storage snapshot: "
            f"{storage_snapshot.approvals} approval(s), {storage_snapshot.jobs} job(s), "
            f"{storage_snapshot.evidence_records} evidence record(s), {storage_snapshot.audit_events} audit event(s)"
        )

        if not decision.allowed:
            self._finish_denied(decision.reason_code, decision.message)
            return

        self.output.append("\nHuman approval artifact:")
        self.output.append(json.dumps(result.approval.to_dict() if result.approval else {}, indent=2, sort_keys=True, default=str))

        job_payload = result.job.to_dict() if result.job else {}
        self.output.append("\nSigned job envelope:")
        self.output.append(json.dumps(job_payload, indent=2, sort_keys=True, default=str))

        for evidence in result.evidence:
            self.output.append("\nEvidence record:")
            self.output.append(json.dumps(evidence.content, indent=2, sort_keys=True, default=str))
            self.output.append(f"Evidence SHA-256: {evidence.sha256}")

        self.progress.setValue(100)
        self.results_label.setText(f"Completed. Evidence records: {len(result.evidence)}")
        self.exec_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if hasattr(self.main, "update_mcp_status"):
            self.main.update_mcp_status(adapter_id, "Success", 100, result=decision.reason_code)
        if hasattr(self.main, "update_intel"):
            self.main.update_intel(f"[{self.mcp['name']}] {decision.reason_code}; {len(result.evidence)} evidence record(s)")
        if hasattr(self.main, "log_message"):
            self.main.log_message(f"Simulator {self.mcp['name']} completed with {decision.reason_code}")

    def stop(self):
        if hasattr(self.main, "_stop_all"):
            self.main._stop_all()
        self.output.append("Queue stop requested. Simulator jobs do not spawn child processes.")

    def _target_from_ui(self):
        if getattr(self.main, "global_target", ""):
            return self.main.global_target
        field = self.fields.get("target")
        return field.text().strip() if field else ""

    def _finish_denied(self, reason_code, message):
        self.progress.setValue(100)
        self.exec_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.results_label.setText(f"Denied: {reason_code}")
        self.output.append(f"Denied: {reason_code} - {message}")
        if hasattr(self.main, "update_mcp_status"):
            self.main.update_mcp_status(self.mcp["id"], "Denied", 100, result=reason_code)
        if hasattr(self.main, "log_message"):
            self.main.log_message(f"Simulator {self.mcp['name']} denied with {reason_code}")
