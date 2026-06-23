"""Canonical 22-MCP adapter catalog for the Grokier control plane."""

from __future__ import annotations

from .p0_models import AdapterManifest

MCP_CATALOG_ORDER: tuple[str, ...] = (
    "a0.fixture.inventory",
    "a1.tls.assessment",
    "a2.dns.posture",
    "a3.http.headers",
    "a4.tls.cert_expiry",
    "a5.port.scan_sim",
    "a6.web.crawl_sim",
    "a7.live.probe",
    "mcp.recon.osint",
    "mcp.recon.subdomain",
    "mcp.network.service",
    "mcp.network.path",
    "mcp.web.fuzzer",
    "mcp.web.inject",
    "mcp.web.auth",
    "mcp.cloud.iam",
    "mcp.cloud.storage",
    "mcp.binary.static",
    "mcp.binary.dynamic",
    "mcp.api.rest",
    "mcp.api.graphql",
    "mcp.evidence.compiler",
)


def _manifest(
    adapter_id: str,
    name: str,
    tier: str,
    execution_mode: str,
    description: str,
    *,
    parameters: tuple[str, ...] = ("target",),
    allowed_target_types: tuple[str, ...] = ("host", "domain", "ip", "cidr", "url"),
    fixture_only: bool = True,
) -> AdapterManifest:
    return AdapterManifest(
        adapter_id=adapter_id,
        name=name,
        version="0.2.0",
        tier=tier,
        execution_mode=execution_mode,
        parameters=parameters,
        allowed_target_types=allowed_target_types,
        network_access=False,
        fixture_only=fixture_only,
        reviewed=True,
        description=description,
    )


def build_mcp_catalog() -> dict[str, AdapterManifest]:
    entries = (
        _manifest(
            "a0.fixture.inventory",
            "A0 Fixture Inventory",
            "A0",
            "offline_fixture",
            "Asset inventory and scope validation against fixture corpora.",
        ),
        _manifest(
            "a1.tls.assessment",
            "A1 TLS Assessment",
            "A1",
            "fake_transport",
            "TLS posture and cipher analysis via fake transport.",
            allowed_target_types=("domain", "url"),
        ),
        _manifest(
            "a2.dns.posture",
            "A2 DNS Posture",
            "A2",
            "offline_fixture",
            "DNSSEC, SPF, DMARC, and CAA intelligence fixtures.",
            allowed_target_types=("domain",),
        ),
        _manifest(
            "a3.http.headers",
            "A3 HTTP Headers",
            "A3",
            "offline_fixture",
            "Security header hardening analysis fixtures.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "a4.tls.cert_expiry",
            "A4 TLS Certificate Expiry",
            "A4",
            "fake_transport",
            "Certificate lifecycle and expiry tracking fixtures.",
            allowed_target_types=("domain", "url"),
        ),
        _manifest(
            "a5.port.scan_sim",
            "A5 Port Scan Simulator",
            "A5",
            "mock_transport",
            "Controlled port and service discovery via mock transport.",
            allowed_target_types=("host", "domain", "ip"),
        ),
        _manifest(
            "a6.web.crawl_sim",
            "A6 Web Crawl Simulator",
            "A6",
            "mock_transport",
            "Web surface mapping via mock crawl transport.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "a7.live.probe",
            "A7 Governed Live Probe",
            "A7",
            "governed_transport",
            "Governed live-transport probe — feature-flagged, ROE-bound.",
            allowed_target_types=("domain",),
            fixture_only=False,
        ),
        _manifest(
            "mcp.recon.osint",
            "MCP Recon OSINT",
            "R1",
            "orchestrated_fixture",
            "OSINT aggregation and entity graph orchestration.",
        ),
        _manifest(
            "mcp.recon.subdomain",
            "MCP Recon Subdomain",
            "R2",
            "orchestrated_fixture",
            "Subdomain enumeration pipeline orchestration.",
        ),
        _manifest(
            "mcp.network.service",
            "MCP Network Service",
            "N1",
            "mock_transport",
            "Service fingerprinting and banner grab simulation.",
            allowed_target_types=("host", "domain", "ip"),
        ),
        _manifest(
            "mcp.network.path",
            "MCP Network Path",
            "N2",
            "mock_transport",
            "Traceroute and path MTU discovery simulation.",
            allowed_target_types=("host", "domain", "ip"),
        ),
        _manifest(
            "mcp.web.fuzzer",
            "MCP Web Fuzzer",
            "W1",
            "mock_transport",
            "Content and parameter fuzzing orchestration.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "mcp.web.inject",
            "MCP Web Inject",
            "W2",
            "mock_transport",
            "Injection-class assessment runner (controlled fixtures).",
            allowed_target_types=("url",),
        ),
        _manifest(
            "mcp.web.auth",
            "MCP Web Auth",
            "W3",
            "orchestrated_fixture",
            "Session and authentication flow analysis.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "mcp.cloud.iam",
            "MCP Cloud IAM",
            "C1",
            "orchestrated_fixture",
            "Cloud IAM posture snapshot orchestration.",
            allowed_target_types=("domain", "url"),
        ),
        _manifest(
            "mcp.cloud.storage",
            "MCP Cloud Storage",
            "C2",
            "orchestrated_fixture",
            "Bucket and blob exposure analysis orchestration.",
            allowed_target_types=("domain", "url"),
        ),
        _manifest(
            "mcp.binary.static",
            "MCP Binary Static",
            "B1",
            "offline_fixture",
            "Static binary and manifest analysis.",
            parameters=("target", "artifact"),
            allowed_target_types=("host", "url"),
        ),
        _manifest(
            "mcp.binary.dynamic",
            "MCP Binary Dynamic",
            "B2",
            "mock_transport",
            "Sandboxed dynamic instrumentation simulation.",
            parameters=("target", "artifact"),
            allowed_target_types=("host", "url"),
        ),
        _manifest(
            "mcp.api.rest",
            "MCP API REST",
            "P1",
            "mock_transport",
            "REST API schema and auth testing simulation.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "mcp.api.graphql",
            "MCP API GraphQL",
            "P2",
            "mock_transport",
            "GraphQL introspection and abuse-case simulation.",
            allowed_target_types=("url",),
        ),
        _manifest(
            "mcp.evidence.compiler",
            "MCP Evidence Compiler",
            "E1",
            "export_compiler",
            "Evidence merge, signing, and report emit pipeline.",
            parameters=("target", "engagement_id"),
            fixture_only=False,
        ),
    )
    catalog = {manifest.adapter_id: manifest for manifest in entries}
    assert len(catalog) == 22
    assert set(catalog) == set(MCP_CATALOG_ORDER)
    return {adapter_id: catalog[adapter_id] for adapter_id in MCP_CATALOG_ORDER}


def catalog_markdown() -> str:
    catalog = build_mcp_catalog()
    lines = [
        "# MasterBlaster MCP Catalog (22)",
        "",
        "| # | MCP ID | Tier | Mode | Name |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for index, adapter_id in enumerate(MCP_CATALOG_ORDER, start=1):
        manifest = catalog[adapter_id]
        lines.append(
            f"| {index:02d} | `{adapter_id}` | {manifest.tier} | "
            f"{manifest.execution_mode} | {manifest.name} |"
        )
    return "\n".join(lines)