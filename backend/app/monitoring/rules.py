from typing import Tuple, Dict, Any
from backend.app.schemas.service import ServiceStatus, ServiceType

def evaluate_raw_check(
    service_type: ServiceType,
    success: bool,
    response_time_ms: float,
    packet_loss_percent: float,
    expected_ms: float,
    warning_ms: float,
    critical_ms: float,
    error: str = None
) -> ServiceStatus:
    """
    Authoritative deterministic rule-based status evaluation for a single raw check result.
    """
    if not success or (error and "down" in str(error).lower()):
        return ServiceStatus.DOWN

    if service_type == ServiceType.PING:
        if packet_loss_percent >= 100.0:
            return ServiceStatus.DOWN
        elif packet_loss_percent > 10.0:
            return ServiceStatus.CRITICAL
        elif packet_loss_percent > 2.0:
            return ServiceStatus.WARNING
        # Check latency if packet loss is minimal
        if response_time_ms > critical_ms:
            return ServiceStatus.CRITICAL
        elif response_time_ms > warning_ms:
            return ServiceStatus.WARNING
        return ServiceStatus.HEALTHY

    # For HTTP, HTTPS, TCP, DNS
    if response_time_ms <= 0:
        return ServiceStatus.DOWN

    if response_time_ms <= expected_ms:
        return ServiceStatus.HEALTHY
    elif response_time_ms <= warning_ms:
        return ServiceStatus.WARNING
    else:
        return ServiceStatus.CRITICAL

def update_anti_flapping_state(
    current_stored_status: ServiceStatus,
    raw_status: ServiceStatus,
    consecutive_failures: int,
    consecutive_successes: int,
    consecutive_failures_down: int = 2,
    consecutive_successes_recovery: int = 2
) -> Tuple[ServiceStatus, int, int, bool]:
    """
    Anti-flapping state machine.
    Prevents single momentary glitch from triggering full DOWN or premature flapping.
    
    Returns:
        (new_status, new_consecutive_failures, new_consecutive_successes, state_changed)
    """
    is_raw_failure = (raw_status == ServiceStatus.DOWN)
    
    if is_raw_failure:
        new_failures = consecutive_failures + 1
        new_successes = 0
        
        # Only transition to DOWN if threshold met
        if current_stored_status != ServiceStatus.DOWN:
            if new_failures >= consecutive_failures_down:
                return ServiceStatus.DOWN, new_failures, new_successes, True
            else:
                # In transient degraded state before confirmed DOWN
                return current_stored_status, new_failures, new_successes, False
        else:
            return ServiceStatus.DOWN, new_failures, new_successes, False
    else:
        # Check was successful (HEALTHY, WARNING, or CRITICAL)
        new_successes = consecutive_successes + 1
        new_failures = 0
        
        if current_stored_status == ServiceStatus.DOWN:
            # Need consecutive successes to recover from DOWN
            if new_successes >= consecutive_successes_recovery:
                return raw_status, new_failures, new_successes, True
            else:
                return ServiceStatus.DOWN, new_failures, new_successes, False
        else:
            state_changed = (current_stored_status != raw_status)
            return raw_status, new_failures, new_successes, state_changed
