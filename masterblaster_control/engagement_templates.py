"""Scoped engagement templates for pentest, application security, and bug bounty work."""

from __future__ import annotations

from dataclasses import dataclass

from .mcp_tool_arsenal import DEFAULT_ASSAULT_CHAIN, FULL_ASSAULT_CHAIN, FULL_REGISTRY_QUEUE


@dataclass(frozen=True)
class EngagementTemplate:
    template_id: str
    name: str
    engagement_type: str
    description: str
    typical_value_usd: str
    duration_days: str
    mcp_chain: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    deliverables: tuple[str, ...]
    scope_guidance: str

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "engagement_type": self.engagement_type,
            "description": self.description,
            "typical_value_usd": self.typical_value_usd,
            "duration_days": self.duration_days,
            "mcp_chain": list(self.mcp_chain),
            "recommended_tools": list(self.recommended_tools),
            "deliverables": list(self.deliverables),
            "scope_guidance": self.scope_guidance,
        }


ENGAGEMENT_TEMPLATES: dict[str, EngagementTemplate] = {
    "external-pentest": EngagementTemplate(
        template_id="external-pentest",
        name="External Network Penetration Test",
        engagement_type="penetration_test",
        description="External-facing reconnaissance, port/service identification, and controlled exploitation simulation.",
        typical_value_usd="$15,000 – $35,000",
        duration_days="3–7 business days",
        mcp_chain=(
            "mcp.recon.subdomain",
            "a2.dns.posture",
            "a5.port.scan_sim",
            "mcp.network.service",
            "mcp.web.fuzzer",
            "mcp.evidence.compiler",
        ),
        recommended_tools=("subfinder", "nmap", "nuclei", "ffuf"),
        deliverables=(
            "Executive summary report (PDF/Markdown)",
            "Technical findings with severity ratings",
            "Remediation recommendations",
            "Evidence package (signed hashes + exports)",
            "Compliance mapping appendix (SOC 2 / ISO / PCI)",
        ),
        scope_guidance="Authorized external IPs, domains, and explicitly listed web applications only.",
    ),
    "web-appsec": EngagementTemplate(
        template_id="web-appsec",
        name="Web Application Security Assessment",
        engagement_type="application_security",
        description="Crawl, fuzz, injection testing, and API review for customer-facing applications.",
        typical_value_usd="$12,000 – $40,000",
        duration_days="5–10 business days",
        mcp_chain=DEFAULT_ASSAULT_CHAIN,
        recommended_tools=("ffuf", "nuclei", "sqlmap", "burp", "gobuster"),
        deliverables=(
            "Application security assessment report",
            "OWASP-aligned finding taxonomy",
            "Proof-of-concept evidence references",
            "Prioritized remediation roadmap",
            "Findings-to-proposal upsell worksheet",
        ),
        scope_guidance="Staging or production URLs listed in signed rules of engagement. No out-of-scope subdomains.",
    ),
    "bug-bounty": EngagementTemplate(
        template_id="bug-bounty",
        name="Bug Bounty / Continuous Testing Sprint",
        engagement_type="bug_bounty",
        description="Rapid iterative testing cycle optimized for high-signal vulnerability discovery.",
        typical_value_usd="$10,000 – $25,000",
        duration_days="2–5 business days per sprint",
        mcp_chain=FULL_ASSAULT_CHAIN,
        recommended_tools=("subfinder", "nuclei", "sqlmap", "ffuf", "burp"),
        deliverables=(
            "Sprint findings report",
            "CSV/JSON export for triage platforms",
            "Severity-scored vulnerability register",
            "Re-test verification checklist",
        ),
        scope_guidance="Program scope document required. In-scope assets only; safe harbor terms acknowledged.",
    ),
    "comprehensive-assessment": EngagementTemplate(
        template_id="comprehensive-assessment",
        name="Comprehensive Security Assessment",
        engagement_type="comprehensive",
        description="Full 22-MCP assessment pipeline for high-value engagements requiring complete coverage.",
        typical_value_usd="$35,000 – $50,000",
        duration_days="7–14 business days",
        mcp_chain=FULL_REGISTRY_QUEUE,
        recommended_tools=("nmap", "nuclei", "sqlmap", "hydra", "prowler", "burp"),
        deliverables=(
            "Board-ready executive summary",
            "Full technical report with evidence index",
            "Compliance control mapping",
            "Remediation implementation proposal",
            "Billable usage summary for finance",
        ),
        scope_guidance="Multi-phase ROE with explicit asset inventory. Change control for production testing.",
    ),
}


def list_templates() -> tuple[EngagementTemplate, ...]:
    return tuple(ENGAGEMENT_TEMPLATES.values())


def get_template(template_id: str) -> EngagementTemplate | None:
    return ENGAGEMENT_TEMPLATES.get(template_id)


def templates_markdown() -> str:
    lines = [
        "# Engagement Templates",
        "",
        "| Template | Type | Typical Value | Duration | MCP Steps |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for template in ENGAGEMENT_TEMPLATES.values():
        lines.append(
            f"| {template.name} | {template.engagement_type} | {template.typical_value_usd} | "
            f"{template.duration_days} | {len(template.mcp_chain)} |"
        )
    return "\n".join(lines)