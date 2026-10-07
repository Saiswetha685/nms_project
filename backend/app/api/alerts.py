from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

def serialize_alert(doc: dict) -> dict:
    d = doc.copy()
    if "_id" in d:
        del d["_id"]
    return d

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    unack_only: bool = Query(default=False),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if unack_only:
        query["acknowledged"] = False
    cursor = db.alerts.find(query).sort("created_at", -1).limit(100)
    alerts = await cursor.to_list(length=100)
    return [serialize_alert(a) for a in alerts]

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    alert = await db.alerts.find_one({"alert_id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    now = datetime.now(timezone.utc)
    ack_by = current_user.get("name") or "Operator"
    await db.alerts.update_one(
        {"alert_id": alert_id},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": ack_by,
                "acknowledged_at": now
            }
        }
    )
    updated = await db.alerts.find_one({"alert_id": alert_id})
    return serialize_alert(updated)
