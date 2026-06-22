# masterblaster_control/mcp_tab.py
# Reusable MCP tab with form, execute, live output.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QTextEdit, QProgressBar, QLabel
from PySide6.QtCore import QProcess

class MCPTab(QWidget):
    def __init__(self, mcp_def, main_window):
        super().__init__()
        self.mcp = mcp_def
        self.main = main_window
        self.process = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        title = QLabel(f"<b>{self.mcp['name']}</b><br>{self.mcp.get('description', '')}")
        lay.addWidget(title)

        form = QFormLayout()
        self.fields = {}
        for p in self.mcp.get("params", ["target"]):
            le = QLineEdit()
            if p == "target":
                le.setText(self.main.global_target)
            self.fields[p] = le
            form.addRow(p.capitalize() + ":", le)
        lay.addLayout(form)

        self.exec_btn = QPushButton(f"🚀 Execute {self.mcp['name']}")
        self.exec_btn.clicked.connect(self.execute)
        lay.addWidget(self.exec_btn)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        lay.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background: #0a0a0a; font-family: Consolas; color: #0f0;")
        lay.addWidget(QLabel("Live Output:"))
        lay.addWidget(self.output)

        self.results_label = QLabel("Results will appear here after execution.")
        lay.addWidget(self.results_label)

    def sync_global_target(self, target):
        if "target" in self.fields:
            self.fields["target"].setText(target)

    def execute(self):
        target = self.main.global_target or self.fields.get("target", QLineEdit()).text().strip()
        if not target:
            self.output.append("ERROR: No target provided.")
            return

        cmd = [self.mcp.get("tool", "echo"), target]
        if "ports" in self.fields:
            cmd += ["-p", self.fields["ports"].text()]
        if "flags" in self.fields and self.fields["flags"].text():
            cmd += self.fields["flags"].text().split()

        self.output.append(f"> Running: {' '.join(cmd)}\n")
        self.progress.setValue(10)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(
            lambda: self.output.append(self.process.readAllStandardOutput().data().decode(errors='ignore'))
        )
        self.process.finished.connect(lambda code: self._on_finished(code))
        self.process.start(cmd[0], cmd[1:])

    def _on_finished(self, exit_code):
        self.progress.setValue(100)
        self.results_label.setText(f"Finished with code {exit_code}. Check output and evidence collector.")
        self.main.log_message(f"MCP {self.mcp['name']} finished (code {exit_code})")
        if self.main.global_target:
            self.main.update_intel(f"[{self.mcp['name']}] Completed against {self.main.global_target}")
