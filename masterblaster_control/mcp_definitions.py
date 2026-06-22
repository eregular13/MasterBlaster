# masterblaster_control/mcp_definitions.py
# Full definitions for 20 MCPs + 2 slots. Pulls from MasterBlaster submodule when possible.

import os
import yaml

MCPS = [
    {"id": "recon_nmap", "name": "Recon-Nmap MCP", "tool": "nmap", "params": ["target", "ports", "flags"], "kali_packages": ["nmap"], "description": "Advanced network discovery and port scanning"},
    {"id": "recon_maltego", "name": "Recon-Maltego OSINT MCP", "tool": "maltego", "params": ["target"], "kali_packages": ["maltego"], "description": "OSINT and link analysis"},
    {"id": "vuln_openvas", "name": "Vuln-OpenVAS MCP", "tool": "openvas", "params": ["target"], "kali_packages": ["openvas"], "description": "Comprehensive vulnerability assessment"},
    {"id": "vuln_nikto", "name": "Vuln-Nikto Web MCP", "tool": "nikto", "params": ["target"], "kali_packages": ["nikto"], "description": "Web server vulnerability scanner"},
    {"id": "web_burp", "name": "Web-Burp Suite Proxy MCP", "tool": "burpsuite", "params": ["target"], "kali_packages": ["burpsuite"], "description": "Web proxy and security testing"},
    {"id": "web_sqlmap", "name": "Web-SQLMap MCP", "tool": "sqlmap", "params": ["target", "options"], "kali_packages": ["sqlmap"], "description": "Automated SQL injection testing"},
    {"id": "web_gobuster", "name": "Web-Gobuster Hybrid MCP", "tool": "gobuster", "params": ["target", "wordlist"], "kali_packages": ["gobuster"], "description": "Directory and file brute forcing"},
    {"id": "exploit_msf", "name": "Exploit-Metasploit Framework MCP", "tool": "msfconsole", "params": ["target", "module"], "kali_packages": ["metasploit-framework"], "description": "Exploitation framework"},
    {"id": "exploit_set", "name": "Exploit-SET Social-Engineering MCP", "tool": "setoolkit", "params": ["target"], "kali_packages": ["set"], "description": "Social engineering toolkit"},
    {"id": "wireless_aircrack", "name": "Wireless-Aircrack-ng Suite MCP", "tool": "aircrack-ng", "params": ["interface", "bssid"], "kali_packages": ["aircrack-ng"], "description": "WiFi security auditing"},
    {"id": "wireless_bettercap", "name": "Wireless-Bettercap MITM MCP", "tool": "bettercap", "params": ["interface"], "kali_packages": ["bettercap"], "description": "MITM and network attacks"},
    {"id": "wireless_yersinia", "name": "Wireless-Yersinia Layer2 MCP", "tool": "yersinia", "params": ["interface"], "kali_packages": ["yersinia"], "description": "Layer 2 attack tool"},
    {"id": "password_john", "name": "Password-John + Hashcat Hybrid MCP", "tool": "john", "params": ["hashfile"], "kali_packages": ["john", "hashcat"], "description": "Password cracking hybrid"},
    {"id": "password_hydra", "name": "Password-Hydra Brute MCP", "tool": "hydra", "params": ["target", "service", "wordlist"], "kali_packages": ["hydra"], "description": "Online password brute forcer"},
    {"id": "password_llmnr", "name": "Password-Responsive LLMNR MCP", "tool": "responder", "params": ["interface"], "kali_packages": ["responder"], "description": "LLMNR/NBT-NS poisoning"},
    {"id": "post_empire", "name": "Post-Empire MCP", "tool": "empire", "params": ["target"], "kali_packages": ["empire"], "description": "Post-exploitation framework"},
    {"id": "forensics_autopsy", "name": "Forensics-Autopsy + Volatility MCP", "tool": "autopsy", "params": ["image"], "kali_packages": ["autopsy", "volatility"], "description": "Disk and memory forensics"},
    {"id": "forensics_foremost", "name": "Forensics-Foremost Carver MCP", "tool": "foremost", "params": ["image"], "kali_packages": ["foremost"], "description": "File carving and recovery"},
    {"id": "sniff_wireshark", "name": "Sniff-Wireshark + tcpdump MCP", "tool": "wireshark", "params": ["interface"], "kali_packages": ["wireshark", "tcpdump"], "description": "Packet capture and analysis"},
    {"id": "reporting_dradis", "name": "Reporting-Dradis + Export MCP", "tool": "dradis", "params": [], "kali_packages": ["dradis"], "description": "Evidence management and reporting"},
    {"id": "future_21", "name": "Future MCP 21 (Expandable)", "tool": "echo", "params": ["target"], "kali_packages": [], "description": "Slot for future MCP"},
    {"id": "future_22", "name": "Future MCP 22 (Expandable)", "tool": "echo", "params": ["target"], "kali_packages": [], "description": "Slot for future MCP"},
]

def load_mcps_from_masterblaster(submodule_path):
    """Attempt to load additional MCP definitions from the MasterBlaster submodule."""
    mcp_dir = os.path.join(submodule_path, "mcps")
    if os.path.isdir(mcp_dir):
        for f in os.listdir(mcp_dir):
            if f.endswith(".yaml") or f.endswith(".yml"):
                try:
                    with open(os.path.join(mcp_dir, f)) as fh:
                        data = yaml.safe_load(fh)
                        if data and isinstance(data, dict):
                            MCPS.append(data)
                except Exception as e:
                    print(f"Failed to load MCP def from {f}: {e}")
    return MCPS

def get_mcp_by_id(mid):
    for m in MCPS:
        if m["id"] == mid:
            return m
    return None
