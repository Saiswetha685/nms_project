from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.schemas.risk import RiskLevel

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    description: Optional[str] = ""

class MLPredictionResponse(BaseModel):
    service_id: str
    service_name: Optional[str] = None
    prediction_time: datetime
    probability_down_next_6h: float
    risk_level: RiskLevel
    model_version: str
    model_type: str
    status: str = "READY"
    top_features: List[FeatureImportanceItem]
    advisory_note: str = "ML prediction is advisory only and does not override authoritative deterministic status."

class MLModelMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: List[List[int]]
    avg_lead_time_minutes: float
    train_rows: int
    val_rows: int
    test_rows: int

class MLModelMetadata(BaseModel):
    model_id: str
    model_type: str
    version: str
    training_start: Optional[datetime] = None
    training_end: Optional[datetime] = None
    feature_list: List[str]
    hyperparameters: Dict[str, Any]
    metrics: MLModelMetrics
    model_path: str
    created_at: datetime
    is_active: bool = True

class ModelComparisonItem(BaseModel):
    model_name: str
    precision: float
    recall: float
    f1: float
    roc_auc: float
    avg_warning_lead_time_minutes: float
    decision_type: str
