from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from backend.app.schemas.service import ServiceStatus, ServiceType

class CheckRecord(BaseModel):
    service_id: str
    timestamp: datetime
    check_type: ServiceType
    success: bool
    status: ServiceStatus
    response_time_ms: float
    packet_loss_percent: float = 0.0
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class CheckQuery(BaseModel):
    service_id: str
    limit: int = 100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
