from fastapi import APIRouter, Depends, HTTPException, Path, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user
from backend.app.demo.simulation import SimulationEngine

router = APIRouter(prefix="/demo", tags=["Demo & Simulation"])

@router.post("/sla-risk/stage/{stage}")
async def trigger_demo_stage(
    stage: int = Path(..., ge=1, le=6, description="Stage 1 (Normal) to Stage 6 (Recovery)"),
    service_id: str = Query(default="svc_student_portal"),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    result = await SimulationEngine.trigger_stage(db, stage, service_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/status")
async def get_demo_status(current_user: dict = Depends(get_current_user)):
    return {
        "current_stage": SimulationEngine.CURRENT_STAGE,
        "stages_available": [
            {"stage": 1, "name": "Normal Baseline"},
            {"stage": 2, "name": "Latency Degradation"},
            {"stage": 3, "name": "Packet Loss Spikes"},
            {"stage": 4, "name": "High SLA Risk (ML Warning)"},
            {"stage": 5, "name": "Outage & SLA Violation"},
            {"stage": 6, "name": "Health Recovery"}
        ]
    }
