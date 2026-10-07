from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.schemas.sla import SLAResponse
from backend.app.schemas.incident import IncidentResponse

class SLAReportItem(BaseModel):
    service_id: str
    service_name: str
    target_sla: float
    actual_sla: float
    downtime_minutes: float
    remaining_budget_minutes: float
    compliance_state: str

class AvailabilityReportItem(BaseModel):
    service_id: str
    service_name: str
    type: str
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percent: float
    total_downtime_minutes: float

class ResponseTimeReportItem(BaseModel):
    service_id: str
    service_name: str
    min_ms: float
    avg_ms: float
    max_ms: float
    p95_ms: float
    threshold_ms: float
    degradation_status: str

class IncidentReportSummary(BaseModel):
    total_incidents: int
    open_incidents: int
    resolved_incidents: int
    avg_mttd_minutes: float
    avg_mttr_minutes: float
    incidents: List[IncidentResponse]

class PredictiveRiskReportItem(BaseModel):
    service_id: str
    service_name: str
    rule_risk: float
    ml_probability: Optional[float]
    forecast_hours: Optional[float]
    combined_risk: float
    risk_level: str
    top_factor: str

class ExecutiveSummary(BaseModel):
    generated_at: datetime
    total_services: int
    healthy_services: int
    warning_services: int
    critical_services: int
    down_services: int
    sla_violations_count: int
    high_risk_services_count: int
    active_incidents_count: int
    average_availability_percent: float
    executive_narrative: str
    attention_areas: List[str]
