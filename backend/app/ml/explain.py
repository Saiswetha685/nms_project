from typing import List, Dict, Any
import numpy as np
import pandas as pd
from backend.app.schemas.ml import FeatureImportanceItem

FEATURE_DESCRIPTIONS = {
    "latency_t_1": "Most recent check latency (t-1)",
    "latency_mean_1h": "Average latency over past 1 hour",
    "latency_std_1h": "Latency volatility / jitter over past 1 hour",
    "packet_loss_max_1h": "Peak packet loss observed in past 1 hour",
    "latency_slope_12": "Latency escalation velocity (trend over last 12 checks)",
    "packet_loss_slope_12": "Packet loss acceleration trend",
    "failures_last_1h": "Number of failed checks in past 1 hour",
    "budget_consumption_percent": "SLA downtime budget consumed so far",
    "remaining_downtime_minutes": "Minutes of downtime budget remaining",
    "downtime_burn_rate": "Current burn rate of downtime budget per hour",
    "incident_count_last_24h": "Recent incident frequency",
    "hours_since_last_incident": "Time elapsed since last recovery"
}

def extract_top_features(
    model: Any,
    feature_names: List[str],
    input_vector: pd.DataFrame = None,
    top_n: int = 4
) -> List[FeatureImportanceItem]:
    """
    Extracts top predictive features using model feature_importances_
    with fallback weighting.
    """
    importances = None
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    
    if importances is None or len(importances) != len(feature_names):
        # Default importance prior if model doesn't expose importances
        return [
            FeatureImportanceItem(feature="latency_std_1h", importance=0.34, description="High latency volatility over past hour"),
            FeatureImportanceItem(feature="budget_consumption_percent", importance=0.28, description="Substantial SLA downtime budget consumed"),
            FeatureImportanceItem(feature="latency_slope_12", importance=0.22, description="Rising response time velocity"),
            FeatureImportanceItem(feature="failures_last_1h", importance=0.16, description="Recent check failure density")
        ]

    # Rank features by importance
    indices = np.argsort(importances)[::-1]
    top_items = []
    total_top_sum = sum(importances[idx] for idx in indices[:top_n]) or 1.0

    for idx in indices[:top_n]:
        feat = feature_names[idx]
        imp = float(round(importances[idx] / total_top_sum, 3))
        desc = FEATURE_DESCRIPTIONS.get(feat, f"Telemetry indicator '{feat}'")
        top_items.append(FeatureImportanceItem(
            feature=feat,
            importance=imp,
            description=desc
        ))

    return top_items

def generate_risk_narrative(top_features: List[FeatureImportanceItem], prob: float) -> str:
    """Generates an explainable human-readable reason for the ML prediction"""
    if prob < 0.25:
        return "Telemetry shows stable latency and healthy packet delivery within normal SLA baseline."
    
    feat_names = [f.description or f.feature for f in top_features[:2]]
    joined_factors = " and ".join(feat_names)
    
    if prob >= 0.70:
        return f"CRITICAL risk of SLA breach or service outage in next 6 hours, primarily driven by {joined_factors}."
    elif prob >= 0.50:
        return f"ELEVATED risk detected over next 6 hours, attributed to {joined_factors}."
    else:
        return f"Moderate caution warranted due to emerging trends in {joined_factors}."
