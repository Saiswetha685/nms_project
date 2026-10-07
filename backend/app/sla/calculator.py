from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from backend.app.schemas.sla import SLAResponse, SLABudget, SLAComplianceState
from backend.app.schemas.service import ServiceStatus

logger = logging.getLogger("sla_predict.sla")

class SLACalculator:
    @staticmethod
    async def calculate_service_sla(
        db: AsyncIOMotorDatabase,
        service: dict
    ) -> SLAResponse:
        """
        Authoritative deterministic SLA and downtime budget computation.
        Uses historical check records within configured sla_window_days.
        """
        service_id = service["service_id"]
        sla_target = float(service.get("sla_target_percent", 99.0))
        window_days = int(service.get("sla_window_days", 30))
        count_degraded = bool(service.get("count_degraded_as_downtime", False))
        check_interval = int(service.get("check_interval_seconds", 30))

        total_window_minutes = window_days * 24.0 * 60.0
        allowed_downtime_minutes = round(total_window_minutes * (1.0 - (sla_target / 100.0)), 2)

        now = datetime.now(timezone.utc)
        start_cutoff = now - timedelta(days=window_days)

        # Query checks in window
        cursor = db.checks.find({
            "service_id": service_id,
            "timestamp": {"$gte": start_cutoff}
        }).sort("timestamp", -1)

        total_checks = 0
        failed_checks = 0
        degraded_checks = 0

        async for check in cursor:
            total_checks += 1
            st = check.get("status")
            if st == ServiceStatus.DOWN.value or not check.get("success", True):
                failed_checks += 1
            elif st == ServiceStatus.CRITICAL.value:
                degraded_checks += 1

        # Fallback if no checks yet recorded
        if total_checks == 0:
            availability_percent = 100.0
            used_downtime_minutes = 0.0
        else:
            effective_failures = failed_checks + (degraded_checks if count_degraded else 0)
            availability_percent = round(max(0.0, min(100.0, ((total_checks - effective_failures) / total_checks) * 100.0)), 3)
            # Estimate used downtime in minutes based on failed checks count and check interval
            used_downtime_minutes = round((effective_failures * check_interval) / 60.0, 2)

        # Budget calculation
        remaining_downtime_minutes = round(max(0.0, allowed_downtime_minutes - used_downtime_minutes), 2)
        if allowed_downtime_minutes > 0:
            budget_consumption_percent = round(min(100.0, (used_downtime_minutes / allowed_downtime_minutes) * 100.0), 2)
        else:
            budget_consumption_percent = 100.0 if used_downtime_minutes > 0 else 0.0

        # Compliance state determination:
        # VIOLATED: actual availability < target OR used downtime > allowed downtime
        # AT_RISK: budget consumed >= 75% OR availability within 0.2% of violation
        # COMPLIANT: comfortably meeting target
        if availability_percent < sla_target or used_downtime_minutes > allowed_downtime_minutes:
            compliance_state = SLAComplianceState.VIOLATED
        elif budget_consumption_percent >= 75.0 or availability_percent <= (sla_target + 0.2):
            compliance_state = SLAComplianceState.AT_RISK
        else:
            compliance_state = SLAComplianceState.COMPLIANT

        budget = SLABudget(
            total_window_minutes=total_window_minutes,
            allowed_downtime_minutes=allowed_downtime_minutes,
            used_downtime_minutes=used_downtime_minutes,
            remaining_downtime_minutes=remaining_downtime_minutes,
            budget_consumption_percent=budget_consumption_percent
        )

        return SLAResponse(
            service_id=service_id,
            service_name=service.get("name"),
            sla_target_percent=sla_target,
            sla_window_days=window_days,
            availability_percent=availability_percent,
            compliance_state=compliance_state,
            budget=budget,
            total_observed_checks=total_checks,
            failed_checks=failed_checks,
            degraded_checks=degraded_checks,
            count_degraded_as_downtime=count_degraded,
            calculated_at=now
        )
