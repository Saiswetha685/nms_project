from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.schemas.risk import CombinedRiskResponse, RiskLevel
from backend.app.risk.rule_engine import RuleRiskEngine
from backend.app.ml.predict import MLPredictor

logger = logging.getLogger("sla_predict.combined_risk")

class CombinedRiskEngine:
    @staticmethod
    async def calculate_combined_risk(
        db: AsyncIOMotorDatabase,
        service: dict,
        sla_data: dict = None,
        forecast_data: dict = None
    ) -> CombinedRiskResponse:
        """
        Combines deterministic rule risk, ML failure probability, and forecast budget pressure.
        Weighted combination:
        - Rule-Based Risk: 45%
        - ML DOWN Probability (0-100): 35%
        - SLA Budget Forecast Pressure: 20%
        """
        service_id = service["service_id"]
        now = datetime.now(timezone.utc)

        # 1. Rule-based risk (authoritative transparent baseline)
        rule_resp = await RuleRiskEngine.compute_rule_risk(db, service, sla_data)
        rule_score = rule_resp.rule_risk

        # 2. ML Probability (0.0 to 1.0)
        ml_prob = None
        ml_level = None
        ml_status = "READY"
        try:
            ml_resp = await MLPredictor.predict_service_risk(db, service, sla_data)
            ml_prob = ml_resp.probability_down_next_6h
            ml_level = ml_resp.risk_level
            ml_score = ml_prob * 100.0
        except Exception as e:
            logger.warning("ML prediction failed (%s), falling back to rule risk only", e)
            ml_status = "FALLBACK_RULE_ONLY"
            ml_score = rule_score

        # 3. Forecast pressure (0 to 100)
        forecast_pressure = 0.0
        if forecast_data and forecast_data.get("hours_to_exhaustion") is not None:
            hours = forecast_data["hours_to_exhaustion"]
            if hours <= 12.0:
                forecast_pressure = 95.0
            elif hours <= 48.0:
                forecast_pressure = 75.0
            elif hours <= 168.0:
                forecast_pressure = 45.0
            else:
                forecast_pressure = 10.0
        elif sla_data and "budget" in sla_data:
            # Approximate from budget consumption
            forecast_pressure = float(sla_data["budget"].get("budget_consumption_percent", 0.0))

        # Weighted combination
        weights = {"rule_weight": 0.45, "ml_weight": 0.35, "forecast_weight": 0.20}
        combined_val = (
            (rule_score * weights["rule_weight"]) +
            (ml_score * weights["ml_weight"]) +
            (forecast_pressure * weights["forecast_weight"])
        )
        combined_score = round(max(0.0, min(100.0, combined_val)), 1)

        # Determine combined level
        if combined_score >= 75.0:
            combined_level = RiskLevel.CRITICAL
        elif combined_score >= 50.0:
            combined_level = RiskLevel.HIGH
        elif combined_score >= 25.0:
            combined_level = RiskLevel.MEDIUM
        else:
            combined_level = RiskLevel.LOW

        return CombinedRiskResponse(
            service_id=service_id,
            service_name=service.get("name"),
            rule_risk=rule_score,
            ml_probability=ml_prob,
            ml_risk_level=ml_level,
            forecast_pressure=round(forecast_pressure, 1),
            combined_risk=combined_score,
            combined_risk_level=combined_level,
            ml_status=ml_status,
            calculated_at=now,
            weights_applied=weights
        )
