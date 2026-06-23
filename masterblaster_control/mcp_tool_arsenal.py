"""Kali-style tool bindings for each of the 22 MCP warlord slots."""

from __future__ import annotations

from .mcp_catalog import MCP_CATALOG_ORDER

# MCP ID → primary offensive / assessment tools orchestrated under the whip
MCP_TOOL_ARSENAL: dict[str, tuple[str, ...]] = {
    "a0.fixture.inventory": ("amass", "theharvester", "assetfinder"),
    "a1.tls.assessment": ("testssl.sh", "sslscan", "sslyze"),
    "a2.dns.posture": ("dig", "dnsenum", "fierce"),
    "a3.http.headers": ("curl", "httpx", "whatweb"),
    "a4.tls.cert_expiry": ("openssl", "certigo", "crt.sh"),
    "a5.port.scan_sim": ("nmap", "rustscan", "masscan"),
    "a6.web.crawl_sim": ("katana", "gau", "hakrawler"),
    "a7.live.probe": ("naabu", "httprobe", "tlsx"),
    "mcp.recon.osint": ("maltego", "recon-ng", "spiderfoot"),
    "mcp.recon.subdomain": ("subfinder", "amass", "assetfinder"),
    "mcp.network.service": ("nmap", "nmap-scripts", "netexec"),
    "mcp.network.path": ("traceroute", "mtr", "hping3"),
    "mcp.web.fuzzer": ("ffuf", "feroxbuster", "gobuster", "nuclei"),
    "mcp.web.inject": ("sqlmap", "commix", "dalfox"),
    "mcp.web.auth": ("hydra", "medusa", "patator"),
    "mcp.cloud.iam": ("prowler", "scout-suite", "pacu"),
    "mcp.cloud.storage": ("trivy", "s3scanner", "cloudmapper"),
    "mcp.binary.static": ("ghidra", "radare2", "binwalk"),
    "mcp.binary.dynamic": ("gdb", "strace", "metasploit"),
    "mcp.api.rest": ("burp", "postman", "arjun"),
    "mcp.api.graphql": ("graphql-voyager", "inql", "clairvoyance"),
    "mcp.evidence.compiler": ("faraday", "dradis", "plextrac"),
}

WARLORD_TAGLINE = "One interface. 22 MCPs. Total domination."

DEFAULT_ASSAULT_CHAIN: tuple[str, ...] = (
    "mcp.recon.subdomain",
    "a5.port.scan_sim",
    "mcp.network.service",
    "a6.web.crawl_sim",
    "mcp.web.fuzzer",
    "mcp.web.inject",
    "mcp.api.rest",
    "mcp.evidence.compiler",
)

# Full warlord strike — 12 MCPs, 30+ tool bindings across recon → network → web → API → evidence
FULL_ASSAULT_CHAIN: tuple[str, ...] = (
    "mcp.recon.osint",
    "mcp.recon.subdomain",
    "a2.dns.posture",
    "a5.port.scan_sim",
    "mcp.network.service",
    "mcp.network.path",
    "a6.web.crawl_sim",
    "mcp.web.fuzzer",
    "mcp.web.inject",
    "mcp.web.auth",
    "mcp.api.rest",
    "mcp.evidence.compiler",
)


def tools_for_mcp(adapter_id: str) -> tuple[str, ...]:
    return MCP_TOOL_ARSENAL.get(adapter_id, ())


def arsenal_markdown() -> str:
    lines = [
        "# MasterBlaster Warlord Arsenal — 22 MCPs × Kali-Grade Tools",
        "",
        f"> {WARLORD_TAGLINE}",
        "",
        "| # | MCP | Tools Under Command |",
        "| ---: | --- | --- |",
    ]
    for index, adapter_id in enumerate(MCP_CATALOG_ORDER, start=1):
        tools = ", ".join(f"`{tool}`" for tool in tools_for_mcp(adapter_id))
        lines.append(f"| {index:02d} | `{adapter_id}` | {tools} |")
    return "\n".join(lines)


def count_bound_tools() -> int:
    return sum(len(tools) for tools in MCP_TOOL_ARSENAL.values())