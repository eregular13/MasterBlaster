<div align="center">

# MasterBlaster
### Security Assessment Control Plane for Professional Services Firms

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![MCPs](https://img.shields.io/badge/MCP%20Orchestration-22-blue.svg)](https://github.com/eregular13/MasterBlaster)
[![Engagements](https://img.shields.io/badge/Engagement%20Templates-4-green.svg)](https://github.com/eregular13/MasterBlaster)
[![Branch](https://img.shields.io/badge/Branch-grokier%2Fmasterblaster-blue.svg)](https://github.com/eregular13/MasterBlaster/tree/grokier/masterblaster)

**Orchestrate 22 MCPs to deliver high-quality penetration tests, application security assessments, and bug bounty sprints — in days, not weeks.**

**Built for $10K–$50K engagements with professional deliverables, audit trails, and consulting upsell workflows.**

[Capabilities](#capabilities) · [Engagement Templates](#engagement-templates) · [Client Workflow](#client-workflow) · [Deploy](#deploy) · [Governance](#governance)

</div>

---

## Business Value

MasterBlaster is a **monetizable control plane** for cybersecurity consulting firms. It compresses assessment delivery timelines, standardizes methodology across consultants, and produces client-ready outputs that drive follow-on revenue.

| Outcome | How MasterBlaster Delivers |
| --- | --- |
| **Faster delivery** | Template-driven MCP pipelines automate recon → scanning → evidence collection |
| **Higher margins** | Repeatable workflows reduce senior consultant hours per engagement |
| **Professional deliverables** | Branded reports with executive summary, severity ratings, remediation guidance |
| **Revenue expansion** | Findings-to-proposal generator surfaces remediation, monitoring, and compliance upsells |
| **Enterprise readiness** | RBAC, audit logs, usage metering, CRM/billing exports, compliance appendices |

---

## Capabilities

| Module | Function |
| --- | --- |
| **22 MCP orchestration** | Recon, network, web, cloud, binary, API, and evidence compilation |
| **Engagement templates** | External pentest, web appsec, bug bounty sprint, comprehensive assessment |
| **Client & project management** | Scoped engagements with contract value tracking |
| **Assessment pipelines** | Automated multi-MCP execution with usage logging |
| **Professional reporting** | Markdown/PDF-ready reports with SOC 2, ISO 27001, PCI mapping |
| **Findings → Proposal** | One-click consulting proposal from assessment findings |
| **Tool integrations** | Governed wrappers for nmap, nuclei, sqlmap, ffuf, burp, and related tooling |
| **Billing hooks** | Usage event logging with CSV export for finance systems |
| **PDF client reports** | Branded cover page, executive summary, signature blocks (ReportLab) |
| **Live tool transport** | Governed nmap/nuclei/sqlmap execution when ROE + feature flag enabled |
| **Invoice export** | Project contract value + usage units CSV for finance |
| **Client portal** | HTML engagement dashboard for stakeholder visibility |
| **Re-test workflow** | Remediation verification campaigns for follow-on billing |
| **Accounting exports** | QuickBooks Online and Xero invoice CSV import |
| **SOW generator** | Proposal → Statement of Work for contract execution |
| **Consultant dashboard** | RBAC utilization metrics per consultant seat |
| **Firm Settings** | Logo upload, signatories, live transport runbook |

### Business-Critical Features (Revenue Impact)

| Feature | Delivery Impact | Revenue / Upsell Impact | Status |
| --- | --- | --- | --- |
| PDF client reports (branded, signatures) | Same-day executive deliverable | Supports $10K–$50K engagement close-out | **v1.2** |
| Live tool transport (governed MCPs) | Real scan data without custom tooling | Enables production pentest billing | **v1.2** |
| Engagement templates + pipelines | 3–7 day delivery vs. 2–3 weeks manual | Higher margin per consultant hour | **v1.1** |
| Findings → Proposal | Automated upsell narrative from evidence | $15K–$80K follow-on remediation SOWs | **v1.1** |
| Proposal → SOW generator | Contract-ready scope in minutes | Accelerates signature on retainer work | **v1.2.1** |
| Client portal (HTML) | Stakeholder visibility without calls | Reduces delivery friction; supports renewals | **v1.2.1** |
| Re-test & validation workflow | Structured remediation verification | Billable re-test engagements ($5K–$15K) | **v1.2.1** |
| QuickBooks / Xero exports | Finance-ready invoicing | Accurate billing; faster cash collection | **v1.2.1** |
| Consultant utilization dashboard | Capacity planning across team | Utilization tracking for margin analysis | **v1.2.1** |
| Usage logging + invoice CSV | Audit-grade billable event trail | Supports T&M and fixed-fee reconciliation | **v1.1** |
| Evidence annex (PDF) | Professional artifact appendix | Increases report credibility with enterprise buyers | **v1.2.1** |
| Firm Settings + logo upload | Consistent brand on all deliverables | Enterprise positioning for larger contracts | **v1.2.1** |

---

## Engagement Templates

| Template | Typical Value | Duration | Pipeline Steps |
| --- | --- | --- | ---: |
| External Network Pentest | $15K – $35K | 3–7 days | 6 |
| Web Application Security | $12K – $40K | 5–10 days | 8 |
| Bug Bounty Sprint | $10K – $25K | 2–5 days | 12 |
| Comprehensive Assessment | $35K – $50K | 7–14 days | 22 |

---

## Client Workflow

```bash
git clone https://github.com/eregular13/MasterBlaster.git
cd MasterBlaster
git checkout grokier/masterblaster
pip install -r requirements.txt

# Create project and run assessment pipeline
python main.py
# Clients & Projects → Create Project → Run Assessment Pipeline → Generate Client Report

# Full simulated paid engagement (project → pipeline → PDF → SOW → exports)
python scripts/run_paid_engagement_demo.py example.com

# CLI report generation
python scripts/generate_client_report.py --client "Acme Corp" --project "Q2 Pentest" --proposal --pdf --csv
```

---

## Deploy

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
python main.py
```

Configure firm branding in `data/business/firm_config.json` (company name, report watermark, hourly rate).

---

## Governance

MasterBlaster requires **signed rules of engagement** for all assessment activity. Scope-locked targets, human approval gates, signed job envelopes, and immutable audit trails support enterprise client requirements.

Read the full policy: [ethics.md](ethics.md)

---

<div align="center">

**MasterBlaster** — *Deliver faster. Report professionally. Grow consulting revenue.*

`grokier/masterblaster`

</div>