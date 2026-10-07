import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_executive_summary_pdf(summary_data: dict) -> bytes:
    """Generates a polished executive summary PDF using ReportLab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=10
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=12,
        spaceAfter=6
    )

    story = []

    # Title & Header
    story.append(Paragraph("SLA-Predict Network Management System", title_style))
    story.append(Paragraph(f"Executive Operations & SLA Compliance Audit Report — Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
    story.append(Spacer(1, 10))

    # Executive Narrative
    story.append(Paragraph("Executive Summary Narrative", section_title))
    story.append(Paragraph(summary_data.get("executive_narrative", ""), body_style))
    story.append(Spacer(1, 10))

    # High-level metrics table
    story.append(Paragraph("System Telemetry Key Metrics", section_title))
    metrics_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Total Monitored Targets", str(summary_data.get("total_services", 0)), "Aggregate Availability", f"{summary_data.get('average_availability_percent', 0.0):.2f}%"],
        ["Healthy Services", str(summary_data.get("healthy_services", 0)), "Confirmed SLA Violations", str(summary_data.get("sla_violations_count", 0))],
        ["Warning / Critical", f"{summary_data.get('warning_services', 0)} / {summary_data.get('critical_services', 0)}", "High SLA-Risk Targets", str(summary_data.get("high_risk_services_count", 0))],
        ["Currently Down", str(summary_data.get("down_services", 0)), "Active NOC Incidents", str(summary_data.get("active_incidents_count", 0))]
    ]
    t = Table(metrics_data, colWidths=[140, 110, 140, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.HexColor('#FFFFFF')])
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Priority Attention Areas
    story.append(Paragraph("Priority Operational Attention Areas", section_title))
    attention_list = summary_data.get("attention_areas", [])
    if attention_list:
        for idx, item in enumerate(attention_list, start=1):
            story.append(Paragraph(f"• <b>Issue {idx}:</b> {item}", body_style))
    else:
        story.append(Paragraph("• No critical SLA anomalies or downtime budget overruns detected.", body_style))

    doc.build(story)
    return buffer.getvalue()
