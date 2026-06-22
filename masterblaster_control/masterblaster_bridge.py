# masterblaster_control/masterblaster_bridge.py
# Full MasterBlaster Direct bridge - scans submodule and launches with bidirectional support.

import os
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QTextEdit, QLineEdit, QHBoxLayout

class MasterBlasterBridge(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.mb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "MasterBlaster"))
        self.scripts = []

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>MasterBlaster Direct Bridge</b><br>Launch scripts from the original MasterBlaster repo. Results feed back into GUI."))

        self.script_list = QListWidget()
        self.script_list.itemDoubleClicked.connect(self._launch_selected)
        lay.addWidget(self.script_list)

        h = QHBoxLayout()
        self.target_override = QLineEdit()
        self.target_override.setPlaceholderText("Override target (optional)")
        h.addWidget(self.target_override)
        self.launch_btn = QPushButton("Launch Selected")
        self.launch_btn.clicked.connect(self._launch_selected)
        h.addWidget(self.launch_btn)
        lay.addLayout(h)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        lay.addWidget(QLabel("Output from MasterBlaster:"))
        lay.addWidget(self.output)

        self.refresh_btn = QPushButton("Refresh Script List from Submodule")
        self.refresh_btn.clicked.connect(self.refresh_scripts)
        lay.addWidget(self.refresh_btn)

        self.refresh_scripts()

    def refresh_scripts(self):
        self.script_list.clear()
        self.scripts = []
        if not os.path.isdir(self.mb_path):
            self.output.append("Submodule not found. Make sure 'git submodule update --init --recursive' was run.")
            return

        for root, dirs, files in os.walk(self.mb_path):
            for f in files:
                if f.endswith(('.py', '.sh', '.rb')):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, self.mb_path)
                    self.scripts.append(full)
                    self.script_list.addItem(rel)

    def _launch_selected(self):
        item = self.script_list.currentItem()
        if not item:
            self.output.append("No script selected.")
            return

        idx = self.script_list.row(item)
        script = self.scripts[idx]
        target = self.target_override.text().strip() or self.main.global_target

        if not target:
            self.output.append("No target provided.")
            return

        self.output.append(f"\n>>> Launching {script} with target {target}\n")

        try:
            # Simple execution - pipe output
            proc = subprocess.Popen([script, target], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(script))
            for line in iter(proc.stdout.readline, ''):
                self.output.append(line.rstrip())
            proc.wait()
            self.output.append(f"\n<<< Finished (code {proc.returncode})\n")
            # Pipe result back
            self.main.update_intel(f"MasterBlaster result from {os.path.basename(script)}: see output")
        except Exception as e:
            self.output.append(f"Error: {e}")
