from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.check import CheckRecord
from backend.app.monitoring.engine import MonitoringEngine

router = APIRouter(tags=["Monitoring & Health Checks"])

def serialize_check(doc: dict) -> dict:
    d = doc.copy()
    if "_id" in d:
        del d["_id"]
    return d

@router.get("/services/{service_id}/checks", response_model=List[CheckRecord])
async def get_service_checks(
    service_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.checks.find({"service_id": service_id}).sort("timestamp", -1).limit(limit)
    checks = await cursor.to_list(length=limit)
    return [serialize_check(c) for c in checks]

@router.get("/services/{service_id}/status")
async def get_service_status(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "service_id": service_id,
        "name": svc.get("name"),
        "type": svc.get("type"),
        "current_state": svc.get("current_state", {})
    }

@router.post("/services/{service_id}/check")
async def trigger_service_check(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    result = await MonitoringEngine.run_single_check(db, svc)
    return serialize_check(result)

@router.post("/monitoring/run-all")
async def run_all_checks(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    await MonitoringEngine.run_all_checks(db)
    return {"message": "All monitoring probes executed successfully"}
