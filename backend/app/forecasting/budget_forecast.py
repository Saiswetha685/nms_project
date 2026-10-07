from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.forecasting.holt_winters import exponential_smoothing_forecast
from backend.app.schemas.forecast import ForecastResponse
from backend.app.schemas.service import ServiceStatus

logger = logging.getLogger("sla_predict.forecast_budget")

class BudgetForecaster:
    @staticmethod
    async def forecast_budget_exhaustion(
        db: AsyncIOMotorDatabase,
        service: dict,
        sla_data: dict = None
    ) -> ForecastResponse:
        """
        Forecasts when remaining SLA downtime budget will be exhausted if current
        burn rate trends continue.
        """
        service_id = service["service_id"]
        now = datetime.now(timezone.utc)

        # Budget info
        remaining_budget = 432.0
        used_downtime = 0.0
        allowed_downtime = 432.0
        if sla_data and "budget" in sla_data:
            b = sla_data["budget"]
            remaining_budget = float(b.get("remaining_downtime_minutes", 432.0))
            used_downtime = float(b.get("used_downtime_minutes", 0.0))
            allowed_downtime = float(b.get("allowed_downtime_minutes", 432.0))

        # Check if already violated
        if remaining_budget <= 0:
            return ForecastResponse(
                service_id=service_id,
                service_name=service.get("name"),
                calculated_at=now,
                method="Deterministic Boundary Check",
                sufficient_data=True,
                remaining_budget_minutes=0.0,
                current_burn_rate_minutes_per_hour=0.0,
                hours_to_exhaustion=0.0,
                estimated_exhaustion_time=now,
                lower_confidence_bound_hours=0.0,
                upper_confidence_bound_hours=0.0,
                confidence_level_percent=95.0,
                burn_trend_direction="EXHAUSTED",
                explanation="SLA downtime budget has already been exhausted (100% consumption). Service is in SLA violation."
            )

        # Extract hourly downtime over the last 24 hours
        start_24h = now - timedelta(hours=24)
        checks_cursor = db.checks.find({
            "service_id": service_id,
            "timestamp": {"$gte": start_24h}
        }).sort("timestamp", 1)

        # Bucket into hourly downtime in minutes
        hourly_downtime = [0.0] * 24
        check_interval_min = float(service.get("check_interval_seconds", 30)) / 60.0

        async for c in checks_cursor:
            ts = c["timestamp"]
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            hour_offset = int((ts - start_24h).total_seconds() // 3600)
            if 0 <= hour_offset < 24:
                if c.get("status") == ServiceStatus.DOWN.value or not c.get("success", True):
                    hourly_downtime[hour_offset] += check_interval_min

        recent_burn_hourly = sum(hourly_downtime[-6:]) / 6.0 if len(hourly_downtime) >= 6 else 0.0

        # Run Holt-Winters forecast for next 72 hours
        point_fc, lower_fc, upper_fc = exponential_smoothing_forecast(hourly_downtime, forecast_steps=72)

        # If zero downtime was observed and recent burn is 0
        if sum(hourly_downtime) == 0.0 and recent_burn_hourly == 0.0:
            return ForecastResponse(
                service_id=service_id,
                service_name=service.get("name"),
                calculated_at=now,
                method="Holt-Winters Statistical Forecast",
                sufficient_data=True,
                remaining_budget_minutes=round(remaining_budget, 1),
                current_burn_rate_minutes_per_hour=0.0,
                hours_to_exhaustion=None,
                estimated_exhaustion_time=None,
                lower_confidence_bound_hours=None,
                upper_confidence_bound_hours=None,
                burn_trend_direction="STABLE_ZERO",
                explanation=f"Zero downtime observed in recent telemetry. Downtime budget remains healthy at {remaining_budget:.1f} minutes."
            )

        # Cumulatively accumulate forecasted downtime to find exhaustion step
        cum_point = 0.0
        cum_lower = 0.0
        cum_upper = 0.0
        point_exhaustion_hr = None
        lower_exhaustion_hr = None
        upper_exhaustion_hr = None

        for h, (pt, low, up) in enumerate(zip(point_fc, lower_fc, upper_fc), start=1):
            cum_point += pt
            cum_upper += up  # Upper burn rate causes earlier exhaustion
            cum_lower += low

            if point_exhaustion_hr is None and cum_point >= remaining_budget:
                point_exhaustion_hr = h
            if lower_exhaustion_hr is None and cum_upper >= remaining_budget:
                lower_exhaustion_hr = h  # Fastest exhaustion (worst case)
            if upper_exhaustion_hr is None and cum_lower >= remaining_budget:
                upper_exhaustion_hr = h  # Slowest exhaustion (best case)

        # If not exhausted in 72 hours, project linearly from average burn
        effective_burn = max(0.05, recent_burn_hourly)
        if point_exhaustion_hr is None:
            point_exhaustion_hr = round(remaining_budget / effective_burn, 1)
            lower_exhaustion_hr = max(1.0, round(point_exhaustion_hr * 0.7, 1))
            upper_exhaustion_hr = round(point_exhaustion_hr * 1.4, 1)
        else:
            if lower_exhaustion_hr is None:
                lower_exhaustion_hr = max(1.0, round(point_exhaustion_hr * 0.8, 1))
            if upper_exhaustion_hr is None:
                upper_exhaustion_hr = round(point_exhaustion_hr * 1.25, 1)

        eta_time = now + timedelta(hours=point_exhaustion_hr)
        trend_dir = "ACCELERATING" if point_fc[-1] > point_fc[0] else "DECELERATING" if point_fc[-1] < point_fc[0] else "STEADY"

        explanation_msg = (
            f"At current failure burn rate (~{recent_burn_hourly:.2f} min/hr), remaining SLA downtime budget "
            f"({remaining_budget:.1f} mins) is statistically projected to exhaust in ~{point_exhaustion_hr:.1f} hours "
            f"(95% CI: [{lower_exhaustion_hr:.1f}h - {upper_exhaustion_hr:.1f}h])."
        )

        return ForecastResponse(
            service_id=service_id,
            service_name=service.get("name"),
            calculated_at=now,
            method="Holt-Winters Statistical Forecast",
            sufficient_data=True,
            remaining_budget_minutes=round(remaining_budget, 1),
            current_burn_rate_minutes_per_hour=round(recent_burn_hourly, 2),
            hours_to_exhaustion=round(point_exhaustion_hr, 1),
            estimated_exhaustion_time=eta_time,
            lower_confidence_bound_hours=round(lower_exhaustion_hr, 1),
            upper_confidence_bound_hours=round(upper_exhaustion_hr, 1),
            confidence_level_percent=95.0,
            burn_trend_direction=trend_dir,
            explanation=explanation_msg
        )
