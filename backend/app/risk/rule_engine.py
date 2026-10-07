from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from backend.app.schemas.risk import SLARiskResponse, RiskBreakdown, RiskLevel
from backend.app.schemas.service import ServiceStatus

logger = logging.getLogger("sla_predict.risk")

class RuleRiskEngine:
    # State tracking for hysteresis: service_id -> bool (is_in_high_risk)
    _hysteresis_state: Dict[str, bool] = {}

    @classmethod
    async def compute_rule_risk(
        cls,
        db: AsyncIOMotorDatabase,
        service: dict,
        sla_data: dict = None
    ) -> SLARiskResponse:
        """
        Computes transparent 0-100 deterministic rule-based SLA risk score.
        Weights:
        - Budget pressure: 40%
        - Failure burn rate (recent 1h/6h): 30%
        - Downtime trend (failure velocity): 15%
        - Latency degradation: 15%
        Includes mandatory guardrails and hysteresis.
        """
        service_id = service["service_id"]
        now = datetime.now(timezone.utc)

        # 1. Budget pressure component (0-100)
        budget_consumption = 0.0
        if sla_data and "budget" in sla_data:
            budget_consumption = float(sla_data["budget"].get("budget_consumption_percent", 0.0))
        budget_risk = min(100.0, max(0.0, budget_consumption))

        # 2. Failure burn rate component (checks in the last 1 hour)
        one_hour_ago = now - timedelta(hours=1)
        recent_checks_cursor = db.checks.find({
            "service_id": service_id,
            "timestamp": {"$gte": one_hour_ago}
        }).sort("timestamp", -1)

        total_1h = 0
        failed_1h = 0
        latencies_1h = []
        async for c in recent_checks_cursor:
            total_1h += 1
            if c.get("status") == ServiceStatus.DOWN.value or not c.get("success", True):
                failed_1h += 1
            if c.get("response_time_ms", 0) > 0:
                latencies_1h.append(c["response_time_ms"])

        if total_1h > 0:
            burn_rate_percent = (failed_1h / total_1h) * 100.0
            burn_risk = min(100.0, burn_rate_percent * 2.5)  # E.g. 40% failure = 100 burn risk
        else:
            burn_risk = 0.0

        # 3. Downtime trend / failure velocity component (comparing last 15 min to prior 45 min)
        fifteen_min_ago = now - timedelta(minutes=15)
        recent_15m_fails = await db.checks.count_documents({
            "service_id": service_id,
            "timestamp": {"$gte": fifteen_min_ago},
            "status": ServiceStatus.DOWN.value
        })
        prior_45m_fails = await db.checks.count_documents({
            "service_id": service_id,
            "timestamp": {"$gte": one_hour_ago, "$lt": fifteen_min_ago},
            "status": ServiceStatus.DOWN.value
        })
        # If failures are accelerating in the last 15 min:
        if recent_15m_fails > (prior_45m_fails / 3.0) and recent_15m_fails > 0:
            trend_risk = min(100.0, recent_15m_fails * 30.0)
        else:
            trend_risk = min(100.0, recent_15m_fails * 15.0)

        # 4. Latency degradation component
        expected_ms = float(service.get("expected_response_ms", 200.0))
        warning_ms = float(service.get("warning_response_ms", 400.0))
        critical_ms = float(service.get("critical_response_ms", 800.0))

        if latencies_1h:
            avg_recent_lat = sum(latencies_1h) / len(latencies_1h)
            if avg_recent_lat <= expected_ms:
                latency_risk = 0.0
            elif avg_recent_lat <= warning_ms:
                # Scaled between 0 and 50
                latency_risk = ((avg_recent_lat - expected_ms) / max(1.0, (warning_ms - expected_ms))) * 50.0
            elif avg_recent_lat <= critical_ms:
                # Scaled between 50 and 85
                latency_risk = 50.0 + ((avg_recent_lat - warning_ms) / max(1.0, (critical_ms - warning_ms))) * 35.0
            else:
                latency_risk = min(100.0, 85.0 + (avg_recent_lat - critical_ms) / 50.0)
        else:
            latency_risk = 0.0

        # Weighted calculation
        raw_score = (
            (budget_risk * 0.40) +
            (burn_risk * 0.30) +
            (trend_risk * 0.15) +
            (latency_risk * 0.15)
        )
        final_score = round(raw_score, 1)

        # Mandatory Guardrails
        guardrail_applied = False
        guardrail_reason = None

        if budget_consumption > 100.0:
            if final_score < 90.0:
                final_score = 90.0
                guardrail_applied = True
                guardrail_reason = "SLA budget exceeded (>100% used): Guardrail sets minimum risk to 90"
        elif budget_consumption >= 90.0:
            if final_score < 75.0:
                final_score = 75.0
                guardrail_applied = True
                guardrail_reason = "SLA budget >=90% consumed: Guardrail sets minimum risk to 75"
        elif budget_consumption >= 75.0:
            if final_score < 50.0:
                final_score = 50.0
                guardrail_applied = True
                guardrail_reason = "SLA budget >=75% consumed: Guardrail sets minimum risk to 50"

        # Hysteresis: enter high-risk at >=50, leave only below 40
        was_high = cls._hysteresis_state.get(service_id, False)
        if was_high:
            if final_score < 40.0:
                is_high = False
            else:
                is_high = True
        else:
            is_high = (final_score >= 50.0)
        cls._hysteresis_state[service_id] = is_high

        # Risk level determination
        if final_score >= 75.0:
            level = RiskLevel.CRITICAL
        elif final_score >= 50.0 or is_high:
            level = RiskLevel.HIGH
        elif final_score >= 25.0:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        breakdown = RiskBreakdown(
            budget_risk=round(budget_risk, 1),
            burn_risk=round(burn_risk, 1),
            trend_risk=round(trend_risk, 1),
            latency_risk=round(latency_risk, 1)
        )

        # Record snapshot in MongoDB for historical replay & charts
        snapshot_doc = {
            "service_id": service_id,
            "timestamp": now,
            "rule_risk": final_score,
            "budget_risk": breakdown.budget_risk,
            "burn_risk": breakdown.burn_risk,
            "trend_risk": breakdown.trend_risk,
            "latency_risk": breakdown.latency_risk,
            "risk_level": level.value,
            "guardrail_applied": guardrail_applied
        }
        await db.sla_risk_snapshots.insert_one(snapshot_doc)

        return SLARiskResponse(
            service_id=service_id,
            service_name=service.get("name"),
            rule_risk=final_score,
            risk_level=level,
            breakdown=breakdown,
            guardrail_applied=guardrail_applied,
            guardrail_reason=guardrail_reason,
            in_high_risk_hysteresis=is_high,
            calculated_at=now
        )
