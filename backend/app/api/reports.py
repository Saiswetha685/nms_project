from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.report import (
    SLAReportItem, AvailabilityReportItem, ResponseTimeReportItem,
    IncidentReportSummary, PredictiveRiskReportItem, ExecutiveSummary
)
from backend.app.reports.generator import ReportGenerator
from backend.app.reports.export_csv import export_items_to_csv
from backend.app.reports.export_pdf import generate_executive_summary_pdf

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/sla", response_model=List[SLAReportItem])
async def get_sla_report(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_sla_report(db)

@router.get("/availability", response_model=List[AvailabilityReportItem])
async def get_availability_report(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_availability_report(db)

@router.get("/response-time", response_model=List[ResponseTimeReportItem])
async def get_response_time_report(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_response_time_report(db)

@router.get("/incidents", response_model=IncidentReportSummary)
async def get_incident_report(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_incident_report(db)

@router.get("/predictive-risk", response_model=List[PredictiveRiskReportItem])
async def get_predictive_risk_report(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_predictive_risk_report(db)

@router.get("/executive-summary", response_model=ExecutiveSummary)
async def get_executive_summary(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    return await ReportGenerator.generate_executive_summary(db)

@router.get("/export/csv")
async def export_csv(
    report_type: str = Query(default="sla", alias="type"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    report_type = report_type.lower()
    if report_type == "sla":
        items = await ReportGenerator.generate_sla_report(db)
        headers = ["Service ID", "Service Name", "Target SLA (%)", "Actual SLA (%)", "Used Downtime (min)", "Remaining Budget (min)", "Compliance State"]
        rows = [[i.service_id, i.service_name, i.target_sla, i.actual_sla, i.downtime_minutes, i.remaining_budget_minutes, i.compliance_state] for i in items]
    elif report_type == "availability":
        items = await ReportGenerator.generate_availability_report(db)
        headers = ["Service ID", "Service Name", "Type", "Total Checks", "Success Checks", "Failed Checks", "Uptime (%)", "Downtime (min)"]
        rows = [[i.service_id, i.service_name, i.type, i.total_checks, i.successful_checks, i.failed_checks, i.uptime_percent, i.total_downtime_minutes] for i in items]
    elif report_type == "risk":
        items = await ReportGenerator.generate_predictive_risk_report(db)
        headers = ["Service ID", "Service Name", "Rule Risk", "ML 6h Probability", "Combined Risk", "Risk Level", "Primary Driver"]
        rows = [[i.service_id, i.service_name, i.rule_risk, i.ml_probability or 0.0, i.combined_risk, i.risk_level, i.top_factor] for i in items]
    else:
        raise HTTPException(status_code=400, detail="Unsupported report type for CSV export. Options: sla, availability, risk")

    csv_data = export_items_to_csv(headers, rows)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sla_predict_{report_type}_report.csv"}
    )

@router.get("/export/pdf")
async def export_pdf(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    summary = await ReportGenerator.generate_executive_summary(db)
    pdf_bytes = generate_executive_summary_pdf(summary.model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=sla_predict_executive_summary.pdf"}
    )
