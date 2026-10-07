from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.sla.calculator import SLACalculator
from backend.app.risk.rule_engine import RuleRiskEngine
from backend.app.ml.predict import MLPredictor
from backend.app.forecasting.budget_forecast import BudgetForecaster
from backend.app.llm.explanation import ExplanationService

router = APIRouter(tags=["AI Operational Explanations"])

@router.get("/services/{service_id}/explanation")
async def get_service_explanation(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    sla_res = await SLACalculator.calculate_service_sla(db, svc)
    rule_res = await RuleRiskEngine.compute_rule_risk(db, svc, sla_res.model_dump())
    ml_res = await MLPredictor.predict_service_risk(db, svc, sla_res.model_dump())
    fc_res = await BudgetForecaster.forecast_budget_exhaustion(db, svc, sla_res.model_dump())
    inc_count = await db.incidents.count_documents({"service_id": service_id, "status": {"$in": ["OPEN", "ACKNOWLEDGED"]}})

    top_factors = [f.model_dump() for f in ml_res.top_features]

    explanation_text = await ExplanationService.get_service_risk_explanation(
        service_name=svc.get("name", service_id),
        service_type=svc.get("type", "HTTP"),
        status=svc.get("current_state", {}).get("status", "HEALTHY"),
        sla_target=sla_res.sla_target_percent,
        availability=sla_res.availability_percent,
        budget_used_percent=sla_res.budget.budget_consumption_percent,
        remaining_budget_mins=sla_res.budget.remaining_downtime_minutes,
        rule_risk=rule_res.rule_risk,
        ml_prob=ml_res.probability_down_next_6h,
        top_factors=top_factors,
        forecast_hours=fc_res.hours_to_exhaustion,
        recent_incident_count=inc_count
    )

    return {
        "service_id": service_id,
        "explanation": explanation_text,
        "model": "claude-3-5-sonnet-20241022 (with deterministic fallback)"
    }
