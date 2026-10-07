from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class SLAComplianceState(str, Enum):
    COMPLIANT = "COMPLIANT"
    AT_RISK = "AT_RISK"
    VIOLATED = "VIOLATED"

class SLABudget(BaseModel):
    total_window_minutes: float
    allowed_downtime_minutes: float
    used_downtime_minutes: float
    remaining_downtime_minutes: float
    budget_consumption_percent: float

class SLAResponse(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    sla_target_percent: float
    sla_window_days: int
    availability_percent: float
    compliance_state: SLAComplianceState
    budget: SLABudget
    total_observed_checks: int
    failed_checks: int
    degraded_checks: int
    count_degraded_as_downtime: bool
    calculated_at: datetime

class SLADailyRecord(BaseModel):
    date: str
    available_minutes: float
    downtime_minutes: float
    availability_percent: float

class SLAOverviewItem(BaseModel):
    service_id: str
    service_name: str
    type: str
    target_percent: float
    actual_percent: float
    compliance_state: SLAComplianceState
    remaining_budget_minutes: float
    budget_consumption_percent: float
    current_status: str
