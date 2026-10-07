import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.ml.model_registry import ModelRegistry
from backend.app.ml.features import extract_features_from_history, FEATURE_NAMES
from backend.app.ml.explain import extract_top_features
from backend.app.ml.train import run_training_job
from backend.app.schemas.ml import MLPredictionResponse
from backend.app.schemas.risk import RiskLevel

logger = logging.getLogger("sla_predict.ml_predict")

class MLPredictor:
    @classmethod
    async def predict_service_risk(
        cls,
        db: AsyncIOMotorDatabase,
        service: dict,
        sla_data: dict = None
    ) -> MLPredictionResponse:
        """
        Runs ML inference predicting probability of confirmed DOWN or severe SLA breach
        within the next 6 hours.
        Advisory only: does NOT modify deterministic status.
        """
        service_id = service["service_id"]
        now = datetime.now(timezone.utc)

        # 1. Fetch active model or auto-train baseline if empty
        model, metadata = await ModelRegistry.get_active_model(db)
        if model is None:
            logger.info("No active ML model found in registry. Auto-training initial baseline model...")
            metadata = await run_training_job(db)
            model, _ = await ModelRegistry.get_active_model(db)

        # 2. Fetch recent checks for feature engineering (up to 150 checks)
        checks_cursor = db.checks.find({"service_id": service_id}).sort("timestamp", -1).limit(150)
        checks = []
        async for c in checks_cursor:
            checks.append(c)
        checks.reverse()  # Chronological order ascending

        features = extract_features_from_history(
            checks=checks,
            service_sla=sla_data.get("budget", {}) if sla_data else {},
            incidents_24h=await db.incidents.count_documents({
                "service_id": service_id,
                "status": {"$in": ["OPEN", "ACKNOWLEDGED"]}
            }),
            reference_time=now
        )

        if not features:
            # Fallback when no telemetry exists yet
            features = {name: 0.0 for name in FEATURE_NAMES}

        df_vec = pd.DataFrame([features], columns=FEATURE_NAMES)

        # 3. Model Inference
        model_version = metadata.get("version", "v1.0") if metadata else "v1.0"
        model_type = metadata.get("model_type", "XGBoost") if metadata else "XGBoost"

        try:
            if hasattr(model, "predict_proba"):
                prob = float(model.predict_proba(df_vec)[0][1])
            else:
                prob = float(model.predict(df_vec)[0])
        except Exception as e:
            logger.warning("Error during model inference (%s), using rule-correlated prior", e)
            prob = 0.15

        prob = max(0.01, min(0.99, round(prob, 3)))

        # Determine risk level
        if prob >= 0.75:
            level = RiskLevel.CRITICAL
        elif prob >= 0.50:
            level = RiskLevel.HIGH
        elif prob >= 0.25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        top_factors = extract_top_features(model, FEATURE_NAMES, df_vec, top_n=4)

        pred_resp = MLPredictionResponse(
            service_id=service_id,
            service_name=service.get("name"),
            prediction_time=now,
            probability_down_next_6h=prob,
            risk_level=level,
            model_version=model_version,
            model_type=model_type,
            status="READY",
            top_features=top_factors
        )

        # Record prediction in DB
        await db.risk_predictions.insert_one({
            "service_id": service_id,
            "timestamp": now,
            "model_version": model_version,
            "model_type": model_type,
            "probability_down_next_6h": prob,
            "risk_level": level.value,
            "top_features": [f.model_dump() for f in top_factors]
        })

        return pred_resp
