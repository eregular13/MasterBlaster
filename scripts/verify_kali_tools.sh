#!/bin/bash
set -euo pipefail

KALI_PACKAGES="nmap metasploit-framework sqlmap gobuster nikto burpsuite aircrack-ng bettercap yersinia john hashcat hydra responder autopsy volatility foremost wireshark tcpdump dradis set"

echo "=== Verify & Install All Kali Tools ==="
sudo apt update
sudo apt install -y $KALI_PACKAGES

echo -e "\n=== Binary Verification ==="
for tool in nmap msfconsole sqlmap gobuster nikto airmon-ng bettercap yersinia john hashcat hydra responder autopsy volatility foremost wireshark tcpdump dradis setoolkit; do
    if command -v $tool &> /dev/null; then
        echo "✓ $tool"
    else
        echo "✗ $tool MISSING"
    fi
done
echo "Done."
