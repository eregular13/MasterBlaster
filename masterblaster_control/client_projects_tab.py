"""Client and project management tab for professional engagements."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .client_projects import create_project, list_projects, projects_markdown
from .engagement_templates import ENGAGEMENT_TEMPLATES
from .pentest_pipeline import execute_assessment_pipeline, pipeline_report_markdown
from .professional_reporting import (
    export_findings_csv,
    export_report_json,
    generate_professional_report,
    professional_report_markdown,
)
from .findings_proposal import generate_consulting_proposal, proposal_markdown
from .usage_logging import export_usage_csv, usage_summary_markdown
from .invoice_export import export_invoice_summary_csv
from .accounting_export import export_quickbooks_csv, export_xero_csv
from .client_portal_dashboard import render_client_portal_html
from .consultant_dashboard import consultant_dashboard_markdown
from .pdf_report_renderer import default_pdf_output_path, render_client_report_pdf
from .retest_workflow import create_retest_campaign, retest_summary_markdown
from .sow_generator import generate_sow_from_report, sow_markdown
from .utils import write_export_file, write_watermarked_report


class ClientProjectsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build_ui()
        self.refresh_projects()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(
            QLabel(
                "<b>Client &amp; Project Management</b><br>"
                "Create scoped engagements from templates. Run assessment pipelines. "
                "Generate client reports and consulting proposals."
            )
        )

        form = QFormLayout()
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("Acme Corporation")
        form.addRow("Client name:", self.client_name)

        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Q2 External Pentest")
        form.addRow("Project name:", self.project_name)

        self.template_combo = QComboBox()
        for template in ENGAGEMENT_TEMPLATES.values():
            self.template_combo.addItem(
                f"{template.name} ({template.typical_value_usd})",
                template.template_id,
            )
        form.addRow("Engagement template:", self.template_combo)

        self.scope_edit = QLineEdit()
        self.scope_edit.setPlaceholderText("example.com, 203.0.113.0/24")
        form.addRow("Scope (comma-separated):", self.scope_edit)

        self.contract_value = QLineEdit()
        self.contract_value.setPlaceholderText("25000")
        form.addRow("Contract value (USD):", self.contract_value)

        self.live_tools_cb = QCheckBox("Authorize live tool transport in ROE (nmap, nuclei, sqlmap)")
        self.live_tools_cb.setToolTip(
            "Enables governed live subprocess execution when live_tool_transport feature flag is on."
        )
        form.addRow("Live tools:", self.live_tools_cb)

        root.addLayout(form)

        buttons = QHBoxLayout()
        create_btn = QPushButton("Create Project")
        create_btn.clicked.connect(self._create_project)
        buttons.addWidget(create_btn)

        run_btn = QPushButton("Run Assessment Pipeline")
        run_btn.clicked.connect(self._run_pipeline)
        buttons.addWidget(run_btn)

        report_btn = QPushButton("Generate Report (Markdown)")
        report_btn.clicked.connect(self._generate_report)
        buttons.addWidget(report_btn)

        pdf_btn = QPushButton("Generate Report (PDF)")
        pdf_btn.clicked.connect(self._generate_pdf_report)
        buttons.addWidget(pdf_btn)

        proposal_btn = QPushButton("Findings → Proposal")
        proposal_btn.clicked.connect(self._generate_proposal)
        buttons.addWidget(proposal_btn)

        sow_btn = QPushButton("Proposal → SOW")
        sow_btn.clicked.connect(self._generate_sow)
        buttons.addWidget(sow_btn)

        root.addLayout(buttons)

        workflow_row = QHBoxLayout()
        portal_btn = QPushButton("Client Portal (HTML)")
        portal_btn.clicked.connect(self._export_portal)
        workflow_row.addWidget(portal_btn)

        retest_btn = QPushButton("Create Re-test Campaign")
        retest_btn.clicked.connect(self._create_retest)
        workflow_row.addWidget(retest_btn)

        util_btn = QPushButton("Consultant Utilization")
        util_btn.clicked.connect(self._show_utilization)
        workflow_row.addWidget(util_btn)
        root.addLayout(workflow_row)

        export_row = QHBoxLayout()
        csv_btn = QPushButton("Export Findings CSV (CRM)")
        csv_btn.clicked.connect(self._export_findings_csv)
        export_row.addWidget(csv_btn)

        usage_btn = QPushButton("Export Usage CSV (Billing)")
        usage_btn.clicked.connect(self._export_usage)
        export_row.addWidget(usage_btn)

        json_btn = QPushButton("Export Report JSON")
        json_btn.clicked.connect(self._export_report_json)
        export_row.addWidget(json_btn)

        invoice_btn = QPushButton("Export Invoice Summary CSV")
        invoice_btn.clicked.connect(self._export_invoice)
        export_row.addWidget(invoice_btn)

        qb_btn = QPushButton("Export QuickBooks CSV")
        qb_btn.clicked.connect(self._export_quickbooks)
        export_row.addWidget(qb_btn)

        xero_btn = QPushButton("Export Xero CSV")
        xero_btn.clicked.connect(self._export_xero)
        export_row.addWidget(xero_btn)
        root.addLayout(export_row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        root.addWidget(self.output, 1)

    def refresh_projects(self):
        self.output.setPlainText(projects_markdown())

    def _selected_project(self):
        projects = list_projects()
        engagement_id = getattr(self.main, "selected_engagement_id", "") or ""
        for project in projects:
            if project.engagement_id == engagement_id:
                return project
        return projects[0] if projects else None

    def _create_project(self):
        client = self.client_name.text().strip()
        project = self.project_name.text().strip()
        scope_raw = self.scope_edit.text().strip()
        if not client or not project or not scope_raw:
            QMessageBox.warning(self, "Validation", "Client name, project name, and scope are required.")
            return
        scope = tuple(s.strip() for s in scope_raw.split(",") if s.strip())
        template_id = self.template_combo.currentData()
        contract = None
        if self.contract_value.text().strip():
            try:
                contract = float(self.contract_value.text().strip())
            except ValueError:
                QMessageBox.warning(self, "Validation", "Contract value must be numeric.")
                return
        try:
            created = create_project(
                self.main.storage,
                client_name=client,
                project_name=project,
                template_id=template_id,
                scope_targets=scope,
                contract_value_usd=contract,
                allow_live_tools=self.live_tools_cb.isChecked(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        self.main.selected_engagement_id = created.engagement_id
        self.main.settings.setValue("selected_engagement_id", created.engagement_id)
        self.main._refresh_engagement_picker()
        self.main.log_message(f"Project created: {created.project_name} ({created.engagement_id})")
        self.refresh_projects()

    def _run_pipeline(self):
        project = self._selected_project()
        if not project:
            QMessageBox.information(self, "Projects", "Create a project first.")
            return
        target = self.main.global_target or (self.scope_edit.text().split(",")[0].strip() or "example.com")
        engagement = self.main.get_active_engagement(target)
        template_id = project.template_id
        try:
            result = execute_assessment_pipeline(
                self.main.runner,
                self.main.storage,
                engagement,
                target,
                template_id,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Pipeline Error", str(exc))
            return
        self.output.setPlainText(pipeline_report_markdown(result, target))
        self.main.log_message(
            f"Pipeline {template_id}: {result.completed} completed, {result.denied} denied"
        )

    def _report_context(self):
        project = self._selected_project()
        client_name = project.client_name if project else "Client"
        project_name = project.project_name if project else "Security Assessment"
        template_id = project.template_id if project else None
        engagement_id = project.engagement_id if project else (
            self.main.selected_engagement_id or "engagement-local-simulator"
        )
        return client_name, project_name, template_id, engagement_id

    def _generate_report(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        md = professional_report_markdown(report)
        path = write_watermarked_report(md, self.main.watermark_enabled, prefix="client_report")
        self.output.setPlainText(md)
        self.main.log_message(f"Client report generated: {path}")
        QMessageBox.information(self, "Report", f"Client report saved:\n{path}")

    def _generate_pdf_report(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        pdf_path = render_client_report_pdf(report, default_pdf_output_path(report))
        self.output.setPlainText(f"PDF report generated: {pdf_path}")
        self.main.log_message(f"Client PDF report: {pdf_path}")
        QMessageBox.information(self, "PDF Report", f"Client PDF saved:\n{pdf_path}")

    def _generate_proposal(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        proposal = generate_consulting_proposal(report)
        md = proposal_markdown(proposal, report)
        path = write_watermarked_report(md, self.main.watermark_enabled, prefix="consulting_proposal")
        self.output.setPlainText(md)
        self.main.log_message(f"Consulting proposal generated: {path}")
        QMessageBox.information(self, "Proposal", f"Proposal saved:\n{path}")

    def _export_findings_csv(self):
        _, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            project_name=project_name,
            template_id=template_id,
        )
        path = write_export_file(export_findings_csv(report), "findings_crm", "csv")
        self.main.log_message(f"Findings CSV exported: {path}")
        QMessageBox.information(self, "Export", f"CRM findings CSV:\n{path}")

    def _export_usage(self):
        project = self._selected_project()
        eid = project.engagement_id if project else None
        path = write_export_file(export_usage_csv(self.main.storage, engagement_id=eid), "usage_billing", "csv")
        summary = usage_summary_markdown(self.main.storage, engagement_id=eid)
        self.output.append("\n" + summary)
        self.main.log_message(f"Usage CSV exported: {path}")
        QMessageBox.information(self, "Export", f"Billing usage CSV:\n{path}")

    def _export_invoice(self):
        path = write_export_file(export_invoice_summary_csv(self.main.storage), "invoice_summary", "csv")
        self.main.log_message(f"Invoice summary exported: {path}")
        QMessageBox.information(self, "Export", f"Invoice summary CSV:\n{path}")

    def _export_report_json(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        path = write_export_file(export_report_json(report), "client_report", "json")
        self.main.log_message(f"Report JSON exported: {path}")
        QMessageBox.information(self, "Export", f"Report JSON:\n{path}")

    def _generate_sow(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        sow, proposal = generate_sow_from_report(report)
        md = sow_markdown(sow, proposal)
        path = write_watermarked_report(md, self.main.watermark_enabled, prefix="statement_of_work")
        self.output.setPlainText(md)
        self.main.log_message(f"SOW generated: {path}")
        QMessageBox.information(self, "SOW", f"Statement of Work saved:\n{path}")

    def _export_portal(self):
        project = self._selected_project()
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        html = render_client_portal_html(self.main.storage, project=project, report=report)
        path = write_export_file(html, "client_portal", "html")
        self.output.setPlainText(f"Client portal exported: {path}")
        self.main.log_message(f"Client portal HTML: {path}")
        QMessageBox.information(self, "Portal", f"Client portal dashboard:\n{path}")

    def _create_retest(self):
        client_name, project_name, template_id, engagement_id = self._report_context()
        report = generate_professional_report(
            self.main.storage,
            engagement_id=engagement_id,
            client_name=client_name,
            project_name=project_name,
            template_id=template_id,
        )
        campaign = create_retest_campaign(report)
        md = retest_summary_markdown(campaign)
        self.output.setPlainText(md)
        self.main.log_message(f"Re-test campaign created: {campaign.campaign_id}")
        QMessageBox.information(self, "Re-test", f"Campaign `{campaign.campaign_id}` created with {len(campaign.items)} items.")

    def _show_utilization(self):
        md = consultant_dashboard_markdown(self.main.storage)
        self.output.setPlainText(md)
        self.main.log_message("Consultant utilization dashboard refreshed")

    def _export_quickbooks(self):
        path = write_export_file(export_quickbooks_csv(self.main.storage), "quickbooks_invoices", "csv")
        self.main.log_message(f"QuickBooks CSV exported: {path}")
        QMessageBox.information(self, "Export", f"QuickBooks invoice CSV:\n{path}")

    def _export_xero(self):
        path = write_export_file(export_xero_csv(self.main.storage), "xero_invoices", "csv")
        self.main.log_message(f"Xero CSV exported: {path}")
        QMessageBox.information(self, "Export", f"Xero invoice CSV:\n{path}")