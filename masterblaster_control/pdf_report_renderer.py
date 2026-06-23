"""Client-facing PDF report generation with branding, cover page, and signature blocks."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .business_config import FirmConfig, load_firm_config
from .engagement_templates import get_template
from .evidence_annex import discover_evidence_images
from .professional_reporting import (
    SEVERITY_ORDER,
    ProfessionalReport,
    _compliance_mapping,
    _remediation_for_finding,
)

SEVERITY_COLORS = {
    "critical": colors.HexColor("#8B0000"),
    "high": colors.HexColor("#CC3300"),
    "medium": colors.HexColor("#E67E22"),
    "low": colors.HexColor("#2980B9"),
    "info": colors.HexColor("#7F8C8D"),
}


def render_client_report_pdf(
    report: ProfessionalReport,
    output_path: str | Path,
    *,
    config: FirmConfig | None = None,
    lead_assessor: str | None = None,
    client_approver: str | None = None,
) -> Path:
    """Render a branded PDF assessment report suitable for client delivery."""
    cfg = config or load_firm_config()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"{report.project_name} — Security Assessment Report",
        author=cfg.firm_name,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e3a5f"),
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story: list = []

    # Cover page
    story.append(Spacer(1, 1.5 * inch))
    if cfg.logo_path and Path(cfg.logo_path).exists():
        from reportlab.platypus import Image

        story.append(Image(cfg.logo_path, width=2 * inch, height=1 * inch))
        story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(cfg.firm_name, title_style))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Security Assessment Report", title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"<b>{report.client_name}</b>", subtitle_style))
    story.append(Paragraph(report.project_name, subtitle_style))
    story.append(Spacer(1, 0.5 * inch))

    template = get_template(report.template_id) if report.template_id else None
    cover_meta = [
        ["Report ID", report.report_id],
        ["Engagement ID", report.engagement_id],
        ["Generated", report.generated_at[:19].replace("T", " ")],
    ]
    if template:
        cover_meta.append(["Assessment Type", template.name])
    cover_table = Table(cover_meta, colWidths=[1.8 * inch, 4.2 * inch])
    cover_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(cover_table)
    story.append(Spacer(1, 0.8 * inch))
    story.append(Paragraph(f"<i>{cfg.report_watermark}</i>", subtitle_style))
    story.append(PageBreak())

    # Executive summary
    story.append(Paragraph("Executive Summary", heading_style))
    total = sum(report.severity_counts.values())
    critical_high = report.severity_counts.get("critical", 0) + report.severity_counts.get("high", 0)
    if total == 0:
        summary = (
            "Assessment activities were executed under authorized scope. No material findings were "
            "identified in this reporting period. We recommend continued monitoring per contract terms."
        )
    else:
        summary = (
            f"This assessment identified {total} observations across in-scope assets. "
            f"{critical_high} finding(s) require priority attention (Critical/High severity). "
            "Detailed findings, evidence references, and remediation guidance follow."
        )
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Findings summary table
    story.append(Paragraph("Findings Summary", heading_style))
    summary_data = [["Severity", "Count"]]
    for level in SEVERITY_ORDER:
        count = report.severity_counts.get(level, 0)
        if count:
            summary_data.append([level.capitalize(), str(count)])
    if len(summary_data) == 1:
        summary_data.append(["—", "0"])
    summary_table = Table(summary_data, colWidths=[2 * inch, 1 * inch])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
        ])
    )
    story.append(summary_table)
    story.append(PageBreak())

    # Detailed findings
    story.append(Paragraph("Detailed Findings", heading_style))
    sorted_findings = sorted(
        report.findings,
        key=lambda f: SEVERITY_ORDER.index(f.severity.lower()) if f.severity.lower() in SEVERITY_ORDER else 99,
    )
    if not sorted_findings:
        story.append(Paragraph("No findings recorded.", body_style))
    else:
        for index, finding in enumerate(sorted_findings, start=1):
            sev_color = SEVERITY_COLORS.get(finding.severity.lower(), colors.black)
            story.append(
                Paragraph(
                    f'<font color="{sev_color.hexval()}"><b>{index}. [{finding.severity.upper()}] '
                    f"{finding.title}</b></font>",
                    body_style,
                )
            )
            story.append(Paragraph(f"<b>Finding ID:</b> {finding.finding_id}", body_style))
            story.append(Paragraph(f"<b>Evidence:</b> {finding.evidence_id}", body_style))
            story.append(Paragraph(f"<b>Confidence:</b> {finding.confidence}", body_style))
            story.append(
                Paragraph(
                    f"<b>Compliance:</b> {', '.join(_compliance_mapping(finding))}",
                    body_style,
                )
            )
            story.append(
                Paragraph(
                    f"<b>Remediation:</b> {_remediation_for_finding(finding)}",
                    body_style,
                )
            )
            story.append(Spacer(1, 0.15 * inch))

    # Evidence annex
    evidence_images = discover_evidence_images(report)
    if evidence_images:
        story.append(PageBreak())
        story.append(Paragraph("Evidence Annex", heading_style))
        story.append(
            Paragraph(
                "The following artifacts support findings documented in this report.",
                body_style,
            )
        )
        story.append(Spacer(1, 0.15 * inch))
        from reportlab.platypus import Image

        for image_path in evidence_images:
            story.append(Paragraph(f"<b>{image_path.name}</b>", body_style))
            try:
                story.append(Image(str(image_path), width=5.5 * inch, height=3 * inch))
            except Exception:
                story.append(Paragraph(f"[Unable to embed: {image_path.name}]", body_style))
            story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())

    # Compliance appendix
    story.append(Paragraph("Compliance Framework Mapping", heading_style))
    story.append(
        Paragraph(
            "Findings may be mapped to SOC 2 Trust Services Criteria, ISO/IEC 27001 Annex A controls, "
            "and PCI-DSS requirements during client quality assurance review.",
            body_style,
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Signatures
    story.append(Paragraph("Authorization & Signatures", heading_style))
    assessor = lead_assessor or getattr(cfg, "lead_assessor_name", "Lead Security Assessor")
    approver = client_approver or getattr(cfg, "client_approver_label", "Client Authorized Representative")
    sig_date = datetime.now().strftime("%Y-%m-%d")
    sig_data = [
        ["Role", "Name", "Signature", "Date"],
        ["Prepared by (Assessor)", assessor, "_________________________", sig_date],
        ["Accepted by (Client)", approver, "_________________________", sig_date],
    ]
    sig_table = Table(sig_data, colWidths=[1.6 * inch, 1.8 * inch, 2 * inch, 0.9 * inch])
    sig_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(sig_table)
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            f"<i>{cfg.firm_name} — {cfg.tagline}</i>",
            ParagraphStyle("Footer", parent=body_style, alignment=TA_CENTER, fontSize=8),
        )
    )

    doc.build(story)
    return path


def default_pdf_output_path(report: ProfessionalReport, prefix: str = "client_report") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("reports") / f"{prefix}_{report.report_id}_{ts}.pdf"