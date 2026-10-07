from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.sla import SLAResponse, SLAOverviewItem, SLADailyRecord
from backend.app.sla.calculator import SLACalculator

router = APIRouter(tags=["SLA Compliance Engine"])

@router.get("/services/{service_id}/sla", response_model=SLAResponse)
async def get_service_sla(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    sla_res = await SLACalculator.calculate_service_sla(db, svc)
    return sla_res

@router.get("/services/{service_id}/sla/history", response_model=List[SLADailyRecord])
async def get_service_sla_history(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    now = datetime.now(timezone.utc)
    history = []
    # Generate past 7 days breakdown
    for day_offset in range(6, -1, -1):
        day_date = now - timedelta(days=day_offset)
        date_str = day_date.strftime("%Y-%m-%d")
        start_ts = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_ts = day_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        total_day_checks = await db.checks.count_documents({
            "service_id": service_id,
            "timestamp": {"$gte": start_ts, "$lte": end_ts}
        })
        failed_day_checks = await db.checks.count_documents({
            "service_id": service_id,
            "timestamp": {"$gte": start_ts, "$lte": end_ts},
            "$or": [{"success": False}, {"status": "DOWN"}]
        })

        if total_day_checks > 0:
            avail = round(((total_day_checks - failed_day_checks) / total_day_checks) * 100.0, 2)
            downtime_min = round(failed_day_checks * (int(svc.get("check_interval_seconds", 30)) / 60.0), 1)
        else:
            avail = 100.0
            downtime_min = 0.0

        history.append(SLADailyRecord(
            date=date_str,
            available_minutes=max(0.0, 1440.0 - downtime_min),
            downtime_minutes=downtime_min,
            availability_percent=avail
        ))
    return history

@router.get("/sla/overview", response_model=List[SLAOverviewItem])
async def get_sla_overview(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.services.find({})
    overview = []
    async for svc in cursor:
        sla_res = await SLACalculator.calculate_service_sla(db, svc)
        overview.append(SLAOverviewItem(
            service_id=svc["service_id"],
            service_name=svc.get("name", svc["service_id"]),
            type=svc.get("type", "HTTP"),
            target_percent=sla_res.sla_target_percent,
            actual_percent=sla_res.availability_percent,
            compliance_state=sla_res.compliance_state,
            remaining_budget_minutes=sla_res.budget.remaining_downtime_minutes,
            budget_consumption_percent=sla_res.budget.budget_consumption_percent,
            current_status=svc.get("current_state", {}).get("status", "HEALTHY")
        ))
    return overview
