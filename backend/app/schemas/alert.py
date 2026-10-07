from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class AlertType(str, Enum):
    SERVICE_DOWN = "SERVICE_DOWN"
    SERVICE_RECOVERY = "SERVICE_RECOVERY"
    SLA_VIOLATION = "SLA_VIOLATION"
    HIGH_SLA_RISK = "HIGH_SLA_RISK"
    CRITICAL_ML_PREDICTION = "CRITICAL_ML_PREDICTION"
    BUDGET_EXHAUSTION_RISK = "BUDGET_EXHAUSTION_RISK"

class AlertResponse(BaseModel):
    alert_id: str
    service_id: str
    service_name: Optional[str] = None
    type: AlertType
    severity: AlertSeverity
    message: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
