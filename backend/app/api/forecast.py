from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.forecast import ForecastResponse
from backend.app.forecasting.budget_forecast import BudgetForecaster
from backend.app.sla.calculator import SLACalculator

router = APIRouter(tags=["Statistical SLA Forecasting"])

@router.get("/services/{service_id}/forecast", response_model=ForecastResponse)
async def get_service_budget_forecast(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    sla_data = await SLACalculator.calculate_service_sla(db, svc)
    return await BudgetForecaster.forecast_budget_exhaustion(db, svc, sla_data.model_dump())
