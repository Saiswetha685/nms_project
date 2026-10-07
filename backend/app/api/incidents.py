from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.schemas.incident import (
    IncidentResponse, IncidentStatus, IncidentAcknowledgeRequest, IncidentResolveRequest
)

router = APIRouter(prefix="/incidents", tags=["Incidents Lifecycle Management"])

def serialize_incident(doc: dict) -> dict:
    d = doc.copy()
    if "_id" in d:
        del d["_id"]
    return d

@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status_filter:
        query["status"] = status_filter.upper()
    cursor = db.incidents.find(query).sort("started_at", -1).limit(100)
    incidents = await cursor.to_list(length=100)
    return [serialize_incident(inc) for inc in incidents]

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    inc = await db.incidents.find_one({"incident_id": incident_id})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return serialize_incident(inc)

@router.post("/{incident_id}/acknowledge", response_model=IncidentResponse)
async def acknowledge_incident(
    incident_id: str,
    ack_req: IncidentAcknowledgeRequest = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    inc = await db.incidents.find_one({"incident_id": incident_id})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now = datetime.now(timezone.utc)
    ack_by = current_user.get("name") or "Operator"
    await db.incidents.update_one(
        {"incident_id": incident_id},
        {
            "$set": {
                "status": IncidentStatus.ACKNOWLEDGED.value,
                "acknowledged_by": ack_by,
                "acknowledged_at": now
            }
        }
    )
    updated = await db.incidents.find_one({"incident_id": incident_id})
    return serialize_incident(updated)

@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    res_req: IncidentResolveRequest = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    inc = await db.incidents.find_one({"incident_id": incident_id})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now = datetime.now(timezone.utc)
    started = inc["started_at"]
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    duration_mins = max(0.1, round((now - started).total_seconds() / 60.0, 2))

    update_payload = {
        "status": IncidentStatus.RESOLVED.value,
        "ended_at": now,
        "resolved_at": now,
        "duration_minutes": duration_mins
    }
    if res_req and res_req.root_cause:
        update_payload["root_cause"] = res_req.root_cause
    if res_req and res_req.resolution_notes:
        update_payload["resolution_notes"] = res_req.resolution_notes

    await db.incidents.update_one({"incident_id": incident_id}, {"$set": update_payload})
    updated = await db.incidents.find_one({"incident_id": incident_id})
    return serialize_incident(updated)
