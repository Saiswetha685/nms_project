import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user, require_admin
from backend.app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceStatus

router = APIRouter(prefix="/services", tags=["Services Registry"])

def serialize_service(doc: dict) -> dict:
    d = doc.copy()
    if "_id" in d:
        del d["_id"]
    return d

@router.get("", response_model=List[ServiceResponse])
async def list_services(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.services.find({}).sort("created_at", -1)
    services = await cursor.to_list(length=200)
    return [serialize_service(s) for s in services]

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    admin_user: dict = Depends(require_admin)
):
    now = datetime.now(timezone.utc)
    service_id = f"svc_{uuid.uuid4().hex[:8]}"

    service_doc = service_in.model_dump()
    service_doc.update({
        "service_id": service_id,
        "current_state": {
            "status": ServiceStatus.UNKNOWN.value,
            "previous_status": ServiceStatus.UNKNOWN.value,
            "response_time_ms": 0.0,
            "packet_loss_percent": 0.0,
            "consecutive_failures": 0,
            "consecutive_successes": 0,
            "last_check": None,
            "last_error": None,
            "in_flapping_state": False
        },
        "created_at": now,
        "updated_at": now
    })

    await db.services.insert_one(service_doc)
    return serialize_service(service_doc)

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return serialize_service(svc)

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    update_in: ServiceUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    admin_user: dict = Depends(require_admin)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    update_data = {k: v for k, v in update_in.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await db.services.update_one({"service_id": service_id}, {"$set": update_data})

    updated_svc = await db.services.find_one({"service_id": service_id})
    return serialize_service(updated_svc)

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    admin_user: dict = Depends(require_admin)
):
    result = await db.services.delete_one({"service_id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    # Clean associated checks & alerts
    await db.checks.delete_many({"service_id": service_id})
    await db.alerts.delete_many({"service_id": service_id})
    await db.incidents.delete_many({"service_id": service_id})
    return None
