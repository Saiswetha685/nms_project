from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from backend.app.database import get_database
from backend.app.auth.deps import get_current_user, require_admin
from backend.app.schemas.ml import MLPredictionResponse, MLModelMetadata, ModelComparisonItem
from backend.app.ml.predict import MLPredictor
from backend.app.ml.train import run_training_job
from backend.app.ml.evaluate import get_model_evaluation_comparison
from backend.app.sla.calculator import SLACalculator

router = APIRouter(prefix="/ml", tags=["Machine Learning Pipeline"])

def serialize_model_meta(doc: dict) -> dict:
    d = doc.copy()
    if "_id" in d:
        del d["_id"]
    return d

@router.get("/services/{service_id}/risk", response_model=MLPredictionResponse)
async def get_service_ml_prediction(
    service_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    svc = await db.services.find_one({"service_id": service_id})
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    sla_data = await SLACalculator.calculate_service_sla(db, svc)
    return await MLPredictor.predict_service_risk(db, svc, sla_data.model_dump())

@router.get("/models")
async def list_models(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    cursor = db.ml_models.find({}).sort("created_at", -1)
    models = await cursor.to_list(length=20)
    return [serialize_model_meta(m) for m in models]

@router.post("/train")
async def trigger_training(
    db: AsyncIOMotorDatabase = Depends(get_database),
    admin_user: dict = Depends(require_admin)
):
    """Admin-triggered training of the Heavy ML pipeline"""
    result = await run_training_job(db)
    return {"message": "Model training pipeline completed successfully", "model_metadata": serialize_model_meta(result)}

@router.get("/evaluation", response_model=List[ModelComparisonItem])
async def get_evaluation_metrics(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    active_doc = await db.ml_models.find_one({"is_active": True}, sort=[("created_at", -1)])
    latest_metrics = active_doc.get("metrics") if active_doc else None
    return get_model_evaluation_comparison(latest_metrics)
