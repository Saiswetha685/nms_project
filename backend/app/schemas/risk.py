from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskBreakdown(BaseModel):
    budget_risk: float = Field(..., description="0-100 score based on downtime budget consumption (weight 40%)")
    burn_risk: float = Field(..., description="0-100 score based on failure burn rate over recent window (weight 30%)")
    trend_risk: float = Field(..., description="0-100 score based on downtime acceleration / failure trend (weight 15%)")
    latency_risk: float = Field(..., description="0-100 score based on latency degradation above warning threshold (weight 15%)")

class SLARiskResponse(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    rule_risk: float
    risk_level: RiskLevel
    breakdown: RiskBreakdown
    guardrail_applied: bool = False
    guardrail_reason: Optional[str] = None
    in_high_risk_hysteresis: bool = False
    calculated_at: datetime

class CombinedRiskResponse(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    rule_risk: float
    ml_probability: Optional[float] = None
    ml_risk_level: Optional[RiskLevel] = None
    forecast_pressure: float
    combined_risk: float
    combined_risk_level: RiskLevel
    ml_status: str
    calculated_at: datetime
    weights_applied: Dict[str, float]
