from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ForecastResponse(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    calculated_at: datetime
    method: str
    sufficient_data: bool
    remaining_budget_minutes: float
    current_burn_rate_minutes_per_hour: float
    hours_to_exhaustion: Optional[float] = None
    estimated_exhaustion_time: Optional[datetime] = None
    lower_confidence_bound_hours: Optional[float] = None
    upper_confidence_bound_hours: Optional[float] = None
    confidence_level_percent: float = 95.0
    burn_trend_direction: str
    explanation: str
    disclaimer: str = "This is a statistical estimate based on historical downtime trend, not a guarantee."
