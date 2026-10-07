from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ServiceType(str, Enum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    PING = "PING"
    TCP = "TCP"
    DNS = "DNS"

class ServiceStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"

class ServiceState(BaseModel):
    status: ServiceStatus = ServiceStatus.UNKNOWN
    previous_status: ServiceStatus = ServiceStatus.UNKNOWN
    response_time_ms: float = 0.0
    packet_loss_percent: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    in_flapping_state: bool = False

class ServiceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""
    type: ServiceType
    target: str = Field(..., description="IP, hostname, or domain")
    port: Optional[int] = Field(None, ge=1, le=65535)
    url: Optional[str] = Field(None, description="Full URL for HTTP/HTTPS")
    enabled: bool = True
    check_interval_seconds: int = Field(default=30, ge=5, le=3600)
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    expected_response_ms: float = Field(default=200.0, ge=1.0)
    warning_response_ms: float = Field(default=400.0, ge=1.0)
    critical_response_ms: float = Field(default=800.0, ge=1.0)
    sla_target_percent: float = Field(default=99.0, ge=50.0, le=100.0)
    sla_window_days: int = Field(default=30, ge=1, le=365)
    count_degraded_as_downtime: bool = False
    consecutive_failures_down: int = Field(default=2, ge=1, le=10)
    consecutive_successes_recovery: int = Field(default=2, ge=1, le=10)
    notification_enabled: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ServiceType] = None
    target: Optional[str] = None
    port: Optional[int] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    check_interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    expected_response_ms: Optional[float] = None
    warning_response_ms: Optional[float] = None
    critical_response_ms: Optional[float] = None
    sla_target_percent: Optional[float] = None
    sla_window_days: Optional[int] = None
    count_degraded_as_downtime: Optional[bool] = None
    consecutive_failures_down: Optional[int] = None
    consecutive_successes_recovery: Optional[int] = None
    notification_enabled: Optional[bool] = None

class ServiceResponse(BaseModel):
    service_id: str
    name: str
    description: Optional[str] = ""
    type: ServiceType
    target: str
    port: Optional[int] = None
    url: Optional[str] = None
    enabled: bool
    check_interval_seconds: int
    timeout_seconds: int
    expected_response_ms: float
    warning_response_ms: float
    critical_response_ms: float
    sla_target_percent: float
    sla_window_days: int
    count_degraded_as_downtime: bool
    consecutive_failures_down: int
    consecutive_successes_recovery: int
    notification_enabled: bool
    current_state: ServiceState
    created_at: datetime
    updated_at: datetime
