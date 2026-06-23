"""Governed live tool execution boundary — isolated subprocess transport for authorized ROE."""

from __future__ import annotations

import shlex
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from .kali_tool_wrappers import KALI_TOOL_REGISTRY, get_tool
from .p0_models import Engagement, EvidenceRecord, JobEnvelope
from .p0_policy import REASON_ALLOW, canonical_json
from .p9_feature_flags import is_feature_enabled


class LiveToolTransportError(Exception):
    def __init__(self, reason_code: str, message: str):
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class LiveExecutionResult:
    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    mode: str  # live | simulated-fallback


def can_execute_live(engagement: Engagement, arguments: dict[str, str]) -> bool:
    """Return True when live execution is permitted and a tool is requested."""
    if not arguments.get("tool"):
        return False
    if not is_feature_enabled("live_tool_transport"):
        return False
    return bool(engagement.rules.allow_network_transport)


def build_live_argv(tool_id: str, target: str, preset_id: str | None = None) -> tuple[str, ...]:
    """Build argv for subprocess without shell interpolation."""
    tool = get_tool(tool_id)
    if tool is None:
        raise LiveToolTransportError("UNKNOWN_TOOL", f"Tool not registered: {tool_id}")

    preset = preset_id or (tool.presets[0].preset_id if tool.presets else None)
    flags: list[str] = []
    if preset:
        for item in tool.presets:
            if item.preset_id == preset:
                flags = shlex.split(item.flags)
                break

    if tool_id == "nmap":
        return (tool.binary, *flags, target)
    if tool_id == "nuclei":
        return (tool.binary, "-u", target, *flags)
    if tool_id == "sqlmap":
        return (tool.binary, "-u", target, *flags)
    if tool_id == "ffuf":
        url = target if target.startswith("http") else f"https://{target}/"
        return (tool.binary, "-u", f"{url}FUZZ", *flags)
    if tool_id == "subfinder":
        return (tool.binary, "-d", target, *flags)
    return (tool.binary, *flags, target)


def _parse_tool_output(tool_id: str, stdout: str, stderr: str, exit_code: int) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = [
        {"id": "live.exit_code", "value": exit_code},
        {"id": "live.stdout_lines", "value": len(stdout.splitlines())},
    ]
    if tool_id == "nmap":
        open_ports = []
        for line in stdout.splitlines():
            if "/tcp" in line and "open" in line:
                port = line.split("/")[0].strip()
                if port.isdigit():
                    open_ports.append(int(port))
        if open_ports:
            observations.append({"id": "port.open", "value": sorted(set(open_ports))})
    if tool_id == "nuclei" and stdout:
        findings = stdout.count("[")
        observations.append({"id": "nuclei.findings", "value": findings})
    if stderr.strip():
        observations.append({"id": "live.stderr_preview", "value": stderr[:500]})
    return observations


def _simulated_fallback(tool_id: str, target: str, reason: str) -> LiveExecutionResult:
    return LiveExecutionResult(
        argv=(tool_id, target),
        exit_code=0,
        stdout=f"[simulated-fallback] {tool_id} against {target}: {reason}",
        stderr="",
        duration_ms=0,
        mode="simulated-fallback",
    )


def execute_live_tool(
    engagement: Engagement,
    job: JobEnvelope,
    *,
    now: datetime | None = None,
) -> EvidenceRecord:
    """Execute a registered security tool under governed transport controls."""
    _ = now or datetime.now(timezone.utc)
    arguments = dict(job.arguments)
    tool_id = str(arguments.get("tool", ""))
    preset_id = str(arguments.get("preset", "")) or None
    target = job.target

    if not can_execute_live(engagement, arguments):
        raise LiveToolTransportError(
            "DENY_LIVE_TRANSPORT",
            "Live tool transport requires feature flag and allow_network_transport in ROE.",
        )

    tool = get_tool(tool_id)
    if tool is None:
        raise LiveToolTransportError("UNKNOWN_TOOL", f"Unknown tool: {tool_id}")

    if tool.binary not in {entry.binary for entry in KALI_TOOL_REGISTRY.values()}:
        raise LiveToolTransportError("DENY_TOOL_BINARY", f"Binary not allowlisted: {tool.binary}")

    argv = build_live_argv(tool_id, target, preset_id)
    binary_path = shutil.which(argv[0])
    started = datetime.now(timezone.utc)

    if binary_path is None:
        result = _simulated_fallback(tool_id, target, f"{argv[0]} not found on PATH")
    else:
        import subprocess

        timeout = min(engagement.rules.max_runtime_seconds, 120)
        try:
            completed = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                check=False,
            )
            elapsed = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            result = LiveExecutionResult(
                argv=tuple(argv),
                exit_code=completed.returncode,
                stdout=completed.stdout[:50_000],
                stderr=completed.stderr[:10_000],
                duration_ms=elapsed,
                mode="live",
            )
        except subprocess.TimeoutExpired:
            result = _simulated_fallback(tool_id, target, f"timeout after {timeout}s")

    observations = _parse_tool_output(tool_id, result.stdout, result.stderr, result.exit_code)
    observations.extend([
        {"id": "live.tool", "value": tool_id},
        {"id": "live.mode", "value": result.mode},
        {"id": "live.command_argv", "value": list(result.argv)},
        {"id": "live.duration_ms", "value": result.duration_ms},
    ])

    content: dict[str, Any] = {
        "adapter_id": job.adapter_id,
        "target": target,
        "transport": "live" if result.mode == "live" else "simulated-fallback",
        "observations": observations,
        "policy_reason": REASON_ALLOW,
        "stdout_preview": result.stdout[:2000],
    }
    digest = sha256(canonical_json(content).encode("utf-8")).hexdigest()
    return EvidenceRecord(
        evidence_id=f"evidence-{digest[:16]}",
        job_id=job.job_id,
        adapter_id=job.adapter_id,
        target=target,
        parser_id=f"parser.live.{tool_id}.v1",
        tool_version="live-1.0",
        sha256=digest,
        content=content,
    )