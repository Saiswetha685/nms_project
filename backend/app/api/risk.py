from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user, require_admin
from backend.app.schemas.risk import SLARiskResponse, CombinedRiskResponse
from backend.app.risk.rule_engine import RuleRiskEngine
from backend.app.risk.combined import CombinedRiskEngine
from backend.app.sla.calculator import SLACalculator

router = APIRouter(tags=["SLA Risk Engine"])

@router.get("/services/{service_id}/sla-risk", response_model=SLARiskResponse)
async def get_service_sla_risk(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    sla_data = await SLACalculator.calculate_service_sla(db, svc)
    return await RuleRiskEngine.compute_rule_risk(db, svc, sla_data.model_dump())

@router.get("/services/{service_id}/combined-risk", response_model=CombinedRiskResponse)
async def get_service_combined_risk(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    sla_data = await SLACalculator.calculate_service_sla(db, svc)
    return await CombinedRiskEngine.calculate_combined_risk(db, svc, sla_data.model_dump())

@router.get("/services/{service_id}/sla-risk/history")
async def get_service_risk_history(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.sla_risk_snapshots.find({"service_id": service_id}).sort("timestamp", -1).limit(60)
    snapshots = await cursor.to_list(length=60)
    # Return chronological ascending
    snapshots.reverse()
    for s in snapshots:
        if "_id" in s:
            del s["_id"]
    return snapshots

@router.get("/sla-risk/overview")
async def get_sla_risk_overview(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.services.find({})
    results = []
    async for svc in cursor:
        sla_data = await SLACalculator.calculate_service_sla(db, svc)
        comb = await CombinedRiskEngine.calculate_combined_risk(db, svc, sla_data.model_dump())
        results.append(comb)
    return results

@router.put("/services/{service_id}/sla-risk/config")
async def update_risk_config(
    service_id: str,
    config: Dict[str, Any] = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_database),
    admin_user: dict = Depends(require_admin)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.services.update_one({"service_id": service_id}, {"$set": {"risk_config": config}})
    return {"message": "Risk configuration updated successfully", "risk_config": config}
