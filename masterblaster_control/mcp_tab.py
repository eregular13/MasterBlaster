# masterblaster_control/mcp_tab.py
# Reusable MCP tab with form, execute, live output, stop, status callbacks.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QTextEdit, QProgressBar, QLabel, QHBoxLayout
from PySide6.QtCore import QProcess, QTimer
import shutil
import os

class MCPTab(QWidget):
    def __init__(self, mcp_def, main_window):
        super().__init__()
        self.mcp = mcp_def
        self.main = main_window
        self.process = None
        self.was_stopped = False
        self._build_ui()
        # Report initial status
        if hasattr(self.main, 'update_mcp_status'):
            self.main.update_mcp_status(self.mcp['id'], 'Idle', 0)

    def _build_ui(self):
        lay = QVBoxLayout(self)

        title = QLabel(f"<b>{self.mcp['name']}</b><br>{self.mcp.get('description', '')}")
        lay.addWidget(title)

        form = QFormLayout()
        self.fields = {}
        for p in self.mcp.get("params", ["target"]):
            le = QLineEdit()
            if p == "target":
                le.setText(self.main.global_target if hasattr(self.main, 'global_target') else "")
            self.fields[p] = le
            form.addRow(p.capitalize() + ":", le)
        lay.addLayout(form)

        btn_layout = QHBoxLayout()
        self.exec_btn = QPushButton(f"🚀 Execute {self.mcp['name']}")
        self.exec_btn.clicked.connect(self.execute)
        btn_layout.addWidget(self.exec_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        lay.addLayout(btn_layout)

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
        if self.process and self.process.state() != QProcess.NotRunning:
            return  # already running

        target = ""
        if hasattr(self.main, 'global_target') and self.main.global_target:
            target = self.main.global_target
        elif "target" in self.fields:
            target = self.fields["target"].text().strip()

        if not target:
            self.output.append("ERROR: No target provided.")
            if hasattr(self.main, 'update_mcp_status'):
                self.main.update_mcp_status(self.mcp['id'], 'Failed', 0)
            return

        tool = self.mcp.get("tool", "echo")
        real_tool = shutil.which(tool) or shutil.which(tool + ".exe")

        # Build base command
        cmd = [tool, target]
        if "ports" in self.fields:
            cmd += ["-p", self.fields["ports"].text()]
        if "flags" in self.fields and self.fields["flags"].text():
            cmd += self.fields["flags"].text().split()

        self.output.append(f"> Running: {' '.join(cmd)}\n")
        self.progress.setValue(10)
        self.was_stopped = False
        if hasattr(self.main, 'update_mcp_status'):
            self.main.update_mcp_status(self.mcp['id'], 'Running', 10)

        if not real_tool:
            # Demo / simulated mode for usability on non-Kali (e.g. Windows dev)
            self.output.append(f"[DEMO MODE] Tool '{tool}' not found in PATH. Using realistic simulated output.\n")
            demo_output = self._get_demo_output(target)
            self.output.append(demo_output + "\n")
            self.progress.setValue(100)
            # Simulate finish
            QTimer.singleShot(200, lambda: self._on_finished(0, 0))
            self.exec_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            return

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(
            lambda: self.output.append(self.process.readAllStandardOutput().data().decode(errors='ignore'))
        )
        self.process.finished.connect(lambda code, status: self._on_finished(code, status))
        self.exec_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.process.start(real_tool, cmd[1:])

    def stop(self):
        """Terminate the running QProcess cleanly. Reports 'Stopped' status."""
        if self.process and self.process.state() != QProcess.NotRunning:
            self.was_stopped = True
            # Prefer terminate (allows graceful on some platforms), fallback to kill
            try:
                self.process.terminate()
            except Exception:
                pass
            # Give it a moment then force kill if still running
            QTimer.singleShot(150, self._force_kill_if_needed)
            self.output.append("\n[STOPPED by user]\n")
            self.progress.setValue(0)
            self.results_label.setText("Stopped by user.")
            if hasattr(self.main, 'update_mcp_status'):
                self.main.update_mcp_status(self.mcp['id'], 'Stopped', 0)
            self.exec_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        else:
            # Ensure UI reset even if no active process
            self.exec_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            if hasattr(self.main, 'update_mcp_status'):
                self.main.update_mcp_status(self.mcp['id'], 'Idle', 0)

    def _on_finished(self, exit_code, exit_status):
        self.progress.setValue(100)
        self.exec_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if getattr(self, 'was_stopped', False):
            status = 'Stopped'
            self.results_label.setText("Process stopped by user.")
            self.was_stopped = False
        else:
            status = 'Success' if exit_code == 0 else 'Failed'
            self.results_label.setText(f"Finished with code {exit_code}. Status: {status}")

        if hasattr(self.main, 'update_mcp_status'):
            self.main.update_mcp_status(self.mcp['id'], status, 100)

        output_text = self.output.toPlainText()
        summary = None

        # Enhanced result parsing + intel for usability
        if "nmap" in self.mcp.get("id", "") or "recon_nmap" in output_text.lower():
            ports = []
            for line in output_text.splitlines():
                if "/tcp" in line and "open" in line:
                    port = line.split("/")[0].strip()
                    ports.append(port)
            if ports:
                summary = f"Open ports: {', '.join(ports[:8])}" + ("..." if len(ports) > 8 else "")
        elif "sqlmap" in self.mcp.get("id", ""):
            if "vulnerable" in output_text.lower() or "injection" in output_text.lower():
                summary = "SQL Injection vulnerability confirmed"
        elif "nikto" in self.mcp.get("id", ""):
            if "vulnerab" in output_text.lower():
                summary = "Web vulnerabilities detected (see output)"
        elif "gobuster" in self.mcp.get("id", ""):
            if "/admin" in output_text or "200" in output_text:
                summary = "Interesting directories discovered"
        elif "hydra" in self.mcp.get("id", "") or "password" in self.mcp.get("id", ""):
            if "password" in output_text.lower() and "login:" in output_text.lower():
                summary = "Weak credentials found"

        if summary:
            self.results_label.setText(summary)
            if hasattr(self.main, 'update_intel'):
                self.main.update_intel(f"[{self.mcp['name']}] {summary}")

        if hasattr(self.main, 'log_message'):
            self.main.log_message(f"MCP {self.mcp['name']} finished (code {exit_code}, status {status})")
        if hasattr(self.main, 'global_target') and self.main.global_target:
            if hasattr(self.main, 'update_intel'):
                self.main.update_intel(f"[{self.mcp['name']}] Completed against {self.main.global_target}")

    def _force_kill_if_needed(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()

    def _get_demo_output(self, target):
        """Return realistic simulated output for demo mode based on MCP type."""
        mcp_id = self.mcp.get("id", "")
        name = self.mcp.get("name", "")
        if "nmap" in mcp_id or "recon" in mcp_id.lower():
            return f"""Starting Nmap 7.94 ( https://nmap.org ) at 2026-06-21
Nmap scan report for {target}
Host is up (0.012s latency).
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
3306/tcp open  mysql
Nmap done: 1 IP address (1 host up) scanned in 1.23 seconds"""
        elif "nikto" in mcp_id or "web" in mcp_id.lower() and "sql" not in mcp_id:
            return f"""- Nikto v2.5.0
+ Target IP:          {target}
+ Target Hostname:    {target}
+ Target Port:        80
+ Server: Apache/2.4.57
+ Retrieved x-powered-by: PHP/8.2
+ OSVDB-3233: /icons/ : Directory indexing found.
+ 5 vulnerabilities found."""
        elif "sqlmap" in mcp_id:
            return f"""[*] starting @ 12:34:56
[12:34:56] [INFO] testing connection to the target URL
[12:34:57] [INFO] checking if the target is protected by some kind of WAF/IPS
[12:34:58] [CRITICAL] {target} is vulnerable to SQL injection! (time-based blind)
[12:34:59] [INFO] fetching banner
web server operating system: Linux
web application technology: Apache 2.4.57, PHP 8.2.7
[12:35:00] [INFO] fetching current user
current user: 'www-data'"""
        elif "gobuster" in mcp_id:
            return f"""Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:                     http://{target}/
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirb/common.txt
[+] Status codes:            200,204,301,302,307,401,403
===============================================================
/admin                (Status: 301)
/login                (Status: 200)
/backup               (Status: 403)
/api/v1               (Status: 200)
===============================================================
Finished"""
        elif "hydra" in mcp_id or "password" in mcp_id.lower():
            return f"""Hydra v9.5 by van Hauser/THC
[DATA] max 16 tasks per 1 server
[DATA] attacking {target}
[22][ssh] host: {target}   login: admin   password: P@ssw0rd123
[STATUS] 23.45 tries/min, 47 tries in 00:02h
[22][ssh] host: {target}   login: root   password: toor"""
        elif "msf" in mcp_id or "exploit" in mcp_id.lower():
            return f"""msf6 > use exploit/multi/handler
[*] Using configured payload generic/shell_reverse_tcp
[*] Started reverse TCP handler on 0.0.0.0:4444 
[*] Sending stage (175174 bytes) to {target}
[*] Meterpreter session 1 opened ({target}:4444 -> local)"""
        elif "wireshark" in mcp_id or "sniff" in mcp_id:
            return "Simulated packet capture: 1423 packets captured. Top talkers: 192.168.1.10, 10.0.0.5. See pcap for details."
        elif "autopsy" in mcp_id or "forensics" in mcp_id:
            return "Forensics scan complete. 3 deleted files recovered. Hash matches found in case database."
        else:
            return f"[{name}] Simulated successful run against {target}.\nOutput: No critical issues found. (demo mode)"
