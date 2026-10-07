import os
import joblib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from backend.app.config import settings

logger = logging.getLogger("sla_predict.ml_registry")

class ModelRegistry:
    _active_model = None
    _active_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    async def save_model(
        cls,
        db: AsyncIOMotorDatabase,
        model_obj: Any,
        model_type: str,
        version: str,
        features: List[str],
        hyperparams: Dict[str, Any],
        metrics: Dict[str, Any],
        train_rows: int
    ) -> Dict[str, Any]:
        """Saves trained model object to disk and registers metadata in MongoDB"""
        model_filename = f"{model_type.lower()}_{version}.joblib"
        file_path = str(settings.ML_MODELS_DIR / model_filename)

        # Save to disk with joblib
        joblib.dump(model_obj, file_path)
        logger.info("Saved serialized model to %s", file_path)

        now = datetime.now(timezone.utc)
        meta_doc = {
            "model_id": f"mdl_{version}",
            "model_type": model_type,
            "version": version,
            "training_start": now,
            "training_end": now,
            "training_rows": train_rows,
            "feature_list": features,
            "hyperparameters": hyperparams,
            "metrics": metrics,
            "model_path": file_path,
            "created_at": now,
            "is_active": True
        }

        # Set any previously active models to inactive
        await db.ml_models.update_many({"is_active": True}, {"$set": {"is_active": False}})
        # Insert new active model
        await db.ml_models.insert_one(meta_doc)

        cls._active_model = model_obj
        cls._active_metadata = meta_doc

        return meta_doc

    @classmethod
    async def get_active_model(cls, db: AsyncIOMotorDatabase = None):
        """Returns loaded model instance and its metadata"""
        if cls._active_model is not None:
            return cls._active_model, cls._active_metadata

        if db is not None:
            active_doc = await db.ml_models.find_one({"is_active": True}, sort=[("created_at", -1)])
            if active_doc and os.path.exists(active_doc.get("model_path", "")):
                try:
                    loaded = joblib.load(active_doc["model_path"])
                    cls._active_model = loaded
                    cls._active_metadata = active_doc
                    return cls._active_model, cls._active_metadata
                except Exception as e:
                    logger.error("Failed loading model from path %s: %s", active_doc.get("model_path"), e)
        return None, None
