"""Governed Kali-grade tool wrappers — commanded through MCP slots, never raw chaos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .mcp_tool_arsenal import WARLORD_TAGLINE
from .p0_approvals import approve_request, request_approval
from .p0_models import Engagement
from .runner_simulator import MANIFESTS, RunnerSimulator
from .warlord_orchestrator import _resolve_target_for_mcp


@dataclass(frozen=True)
class ToolPreset:
    preset_id: str
    label: str
    flags: str
    description: str


@dataclass(frozen=True)
class KaliToolWrapper:
    tool_id: str
    display_name: str
    binary: str
    category: str
    mcp_adapter_id: str
    command_template: str
    presets: tuple[ToolPreset, ...]
    danger_level: str = "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "display_name": self.display_name,
            "binary": self.binary,
            "category": self.category,
            "mcp_adapter_id": self.mcp_adapter_id,
            "command_template": self.command_template,
            "danger_level": self.danger_level,
            "presets": [
                {
                    "preset_id": preset.preset_id,
                    "label": preset.label,
                    "flags": preset.flags,
                    "description": preset.description,
                }
                for preset in self.presets
            ],
        }


def _p(preset_id: str, label: str, flags: str, description: str) -> ToolPreset:
    return ToolPreset(preset_id, label, flags, description)


KALI_TOOL_REGISTRY: dict[str, KaliToolWrapper] = {
    "nmap": KaliToolWrapper(
        "nmap", "Nmap", "nmap", "Network",
        "a5.port.scan_sim", "{binary} {flags} -oN - {target}",
        (
            _p("syn-top", "SYN Top Ports", "-sS -T4 --top-ports 1000", "Fast SYN sweep of top 1000 ports"),
            _p("full-tcp", "Full TCP", "-sS -sV -O -p-", "Full TCP service + OS fingerprint"),
            _p("udp-top", "UDP Top", "-sU --top-ports 100", "UDP top-port discovery"),
        ),
    ),
    "rustscan": KaliToolWrapper(
        "rustscan", "RustScan", "rustscan", "Network",
        "a5.port.scan_sim", "{binary} -a {target} {flags}",
        (_p("fast", "Blitz", "-- -sV", "Ultra-fast port discovery then nmap service scan"),),
    ),
    "nuclei": KaliToolWrapper(
        "nuclei", "Nuclei", "nuclei", "Web",
        "mcp.web.fuzzer", "{binary} -u {target} {flags}",
        (
            _p("critical", "Critical CVEs", "-severity critical,high", "Critical and high severity templates"),
            _p("full", "Full Template Run", "-t exposures/,cves/,misconfiguration/", "Broad template assault"),
        ),
    ),
    "ffuf": KaliToolWrapper(
        "ffuf", "ffuf", "ffuf", "Web",
        "mcp.web.fuzzer", "{binary} -u {target}/FUZZ {flags}",
        (
            _p("dir-bust", "Dir Bust", "-w /usr/share/wordlists/dirb/common.txt -fc 404", "Directory brute force"),
            _p("vhost", "VHost Fuzz", "-w vhosts.txt -H 'Host: FUZZ.{target}'", "Virtual host discovery"),
        ),
    ),
    "gobuster": KaliToolWrapper(
        "gobuster", "Gobuster", "gobuster", "Web",
        "mcp.web.fuzzer", "{binary} dir -u {target} {flags}",
        (_p("dir", "Dir Mode", "-w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt", "Directory enumeration"),),
    ),
    "sqlmap": KaliToolWrapper(
        "sqlmap", "SQLMap", "sqlmap", "Web",
        "mcp.web.inject", "{binary} -u {target} {flags}",
        (
            _p("crawl-inject", "Crawl + Inject", "--crawl=2 --batch --level=3", "Crawl and SQL injection sweep"),
            _p("dump", "Dump Tables", "--batch --dump", "Enumerate and dump database tables"),
        ),
        danger_level="critical",
    ),
    "hydra": KaliToolWrapper(
        "hydra", "Hydra", "hydra", "Auth",
        "mcp.web.auth", "{binary} -L users.txt -P pass.txt {target} {flags}",
        (_p("http-post", "HTTP POST", "http-post-form '/login:user=^USER^&pass=^PASS^:F=invalid'", "HTTP form brute force"),),
        danger_level="critical",
    ),
    "metasploit": KaliToolWrapper(
        "metasploit", "Metasploit", "msfconsole", "Exploit",
        "mcp.binary.dynamic", "{binary} -q -x '{flags}'",
        (
            _p("aux-scan", "Auxiliary Scan", "use auxiliary/scanner/http/http_version; run", "HTTP version auxiliary module"),
            _p("exploit-check", "Exploit Check", "use exploit/multi/handler; check", "Exploit module validation (governed)"),
        ),
        danger_level="critical",
    ),
    "burp": KaliToolWrapper(
        "burp", "Burp Suite", "burpsuite", "API",
        "mcp.api.rest", "{binary} --project-file=mb-{target}.burp {flags}",
        (_p("spider", "Spider Target", "--task=spider --url={target}", "Burp spider through MCP REST bridge"),),
    ),
    "subfinder": KaliToolWrapper(
        "subfinder", "Subfinder", "subfinder", "Recon",
        "mcp.recon.subdomain", "{binary} -d {target} {flags}",
        (_p("all", "All Sources", "-all -recursive", "Maximum subdomain enumeration sources"),),
    ),
    "amass": KaliToolWrapper(
        "amass", "Amass", "amass", "Recon",
        "mcp.recon.subdomain", "{binary} enum -d {target} {flags}",
        (_p("intel", "Intel Mode", "-intel -whois", "OSINT intel pass on domain"),),
    ),
    "masscan": KaliToolWrapper(
        "masscan", "Masscan", "masscan", "Network",
        "a5.port.scan_sim", "{binary} {target} {flags}",
        (_p("internet", "Internet Speed", "-p0-65535 --rate 10000", "High-speed full port scan"),),
    ),
    "feroxbuster": KaliToolWrapper(
        "feroxbuster", "Feroxbuster", "feroxbuster", "Web",
        "mcp.web.fuzzer", "{binary} -u {target} {flags}",
        (_p("recursive", "Recursive", "-w /usr/share/wordlists/dirb/common.txt --depth 4", "Recursive content discovery"),),
    ),
    "commix": KaliToolWrapper(
        "commix", "Commix", "commix", "Web",
        "mcp.web.inject", "{binary} -u {target} {flags}",
        (_p("os-cmd", "OS Command", "--batch --level=3", "OS command injection detection"),),
    ),
    "netexec": KaliToolWrapper(
        "netexec", "NetExec", "netexec", "Network",
        "mcp.network.service", "{binary} smb {target} {flags}",
        (_p("shares", "SMB Shares", "--shares", "Enumerate SMB shares and permissions"),),
    ),
    "prowler": KaliToolWrapper(
        "prowler", "Prowler", "prowler", "Cloud",
        "mcp.cloud.iam", "{binary} aws {flags}",
        (_p("cis", "CIS Benchmark", "--checks cis_1.4_aws", "AWS CIS benchmark assessment"),),
    ),
    "ghidra": KaliToolWrapper(
        "ghidra", "Ghidra", "ghidra", "Binary",
        "mcp.binary.static", "{binary} {flags} {target}",
        (_p("analyze", "Headless Analyze", "analyzeHeadless /tmp proj -import", "Static binary analysis headless"),),
    ),
}


@dataclass(frozen=True)
class ToolUnleashResult:
    tool_id: str
    display_name: str
    mcp_adapter_id: str
    preset_id: str | None
    command: str
    status: str
    reason_code: str
    evidence_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "display_name": self.display_name,
            "mcp_adapter_id": self.mcp_adapter_id,
            "preset_id": self.preset_id,
            "command": self.command,
            "status": self.status,
            "reason_code": self.reason_code,
            "evidence_id": self.evidence_id,
        }


def list_tools(*, category: str | None = None) -> tuple[KaliToolWrapper, ...]:
    tools = tuple(KALI_TOOL_REGISTRY.values())
    if category:
        return tuple(tool for tool in tools if tool.category.lower() == category.lower())
    return tools


def get_tool(tool_id: str) -> KaliToolWrapper | None:
    return KALI_TOOL_REGISTRY.get(tool_id)


def build_command(tool: KaliToolWrapper, target: str, preset_id: str | None = None) -> tuple[str, str | None]:
    flags = ""
    selected = preset_id
    if preset_id:
        for preset in tool.presets:
            if preset.preset_id == preset_id:
                flags = preset.flags
                break
    elif tool.presets:
        flags = tool.presets[0].flags
        selected = tool.presets[0].preset_id
    command = (
        tool.command_template.format(binary=tool.binary, flags=flags, target=target)
        .replace("  ", " ")
        .strip()
    )
    return command, selected


def unleash_tool(
    runner: RunnerSimulator,
    engagement: Engagement,
    target: str,
    tool_id: str,
    *,
    preset_id: str | None = None,
    now: datetime | None = None,
) -> ToolUnleashResult:
    """Route a Kali tool strike through its governing MCP with approval + evidence."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    tool = KALI_TOOL_REGISTRY.get(tool_id)
    if tool is None:
        return ToolUnleashResult(
            tool_id, tool_id, "", preset_id, "", "denied", "UNKNOWN_TOOL", None
        )

    manifest = MANIFESTS.get(tool.mcp_adapter_id)
    if manifest is None:
        return ToolUnleashResult(
            tool.tool_id, tool.display_name, tool.mcp_adapter_id, preset_id, "",
            "denied", "UNKNOWN_MCP", None,
        )

    strike_target = _resolve_target_for_mcp(manifest, target)
    command, selected_preset = build_command(tool, strike_target, preset_id)
    approval = approve_request(
        request_approval(engagement, tool.mcp_adapter_id, strike_target, now=current),
        now=current,
    )
    result = runner.run(
        tool.mcp_adapter_id,
        strike_target,
        engagement=engagement,
        approval=approval,
        arguments={
            "target": strike_target,
            "tool": tool.tool_id,
            "binary": tool.binary,
            "preset": selected_preset or "",
            "command": command,
        },
        now=current,
    )
    evidence_id = result.evidence[0].evidence_id if result.evidence else None
    return ToolUnleashResult(
        tool_id=tool.tool_id,
        display_name=tool.display_name,
        mcp_adapter_id=tool.mcp_adapter_id,
        preset_id=selected_preset,
        command=command,
        status=result.status,
        reason_code=result.decision.reason_code,
        evidence_id=evidence_id,
    )


def unleash_arsenal(
    runner: RunnerSimulator,
    engagement: Engagement,
    target: str,
    *,
    tool_ids: tuple[str, ...] | None = None,
    now: datetime | None = None,
) -> tuple[ToolUnleashResult, ...]:
    """Unleash multiple tools in sequence through their MCP governors."""
    selected = tool_ids or tuple(KALI_TOOL_REGISTRY.keys())
    return tuple(
        unleash_tool(runner, engagement, target, tool_id, now=now) for tool_id in selected
    )


def tool_arsenal_markdown() -> str:
    lines = [
        "# MasterBlaster Kali Tool Arsenal",
        "",
        f"> {WARLORD_TAGLINE}",
        "",
        f"**Governed wrappers:** {len(KALI_TOOL_REGISTRY)}",
        "",
        "| Tool | Category | MCP | Presets | Danger |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for tool in KALI_TOOL_REGISTRY.values():
        lines.append(
            f"| **{tool.display_name}** | {tool.category} | `{tool.mcp_adapter_id}` | "
            f"{len(tool.presets)} | {tool.danger_level} |"
        )
    return "\n".join(lines)