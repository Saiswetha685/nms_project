from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IncidentCreate(BaseModel):
    service_id: str
    severity: IncidentSeverity = IncidentSeverity.CRITICAL
    description: str
    root_cause: Optional[str] = "Service connectivity check failed consecutively"

class IncidentResponse(BaseModel):
    incident_id: str
    service_id: str
    service_name: Optional[str] = None
    started_at: datetime
    detected_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    severity: IncidentSeverity
    status: IncidentStatus
    root_cause: Optional[str] = None
    description: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class IncidentAcknowledgeRequest(BaseModel):
    acknowledged_by: Optional[str] = "operator"
    notes: Optional[str] = None

class IncidentResolveRequest(BaseModel):
    root_cause: Optional[str] = None
    resolution_notes: Optional[str] = None
