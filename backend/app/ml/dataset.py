import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Tuple, List, Dict, Any
from backend.app.ml.features import extract_features_from_history, FEATURE_NAMES

def generate_synthetic_training_data(num_samples: int = 600) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generates a realistic, time-series ordered dataset with pre-failure signatures
    for machine learning training and evaluation in demo/college environments.
    Guarantees no lookahead target leakage.
    """
    random.seed(42)
    np.random.seed(42)

    data_rows = []
    labels = []

    base_time = datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
    current_time = base_time

    # We will simulate normal periods, deteriorating periods (latency spikes, packet loss), and failures
    in_degradation = False
    degradation_countdown = 0

    checks_history = []
    
    # Pre-populate initial 50 checks
    for i in range(50):
        t = current_time - timedelta(minutes=(50 - i) * 5)
        checks_history.append({
            "timestamp": t,
            "response_time_ms": random.uniform(30.0, 75.0),
            "packet_loss_percent": 0.0,
            "success": True,
            "status": "HEALTHY"
        })

    budget_used = 12.0

    for step in range(num_samples):
        current_time += timedelta(minutes=15)
        
        # Decide if entering degradation state
        if not in_degradation and random.random() < 0.12:
            in_degradation = True
            degradation_countdown = random.randint(4, 12) # 1 to 3 hours of warning signs

        if in_degradation:
            degradation_countdown -= 1
            # Rising latency and occasional packet loss
            lat = random.uniform(220.0, 850.0) + (12 - degradation_countdown) * 35.0
            pkl = min(40.0, random.uniform(0.0, 15.0) + (12 - degradation_countdown) * 2.5)
            status = "CRITICAL" if lat > 450.0 else "WARNING"
            budget_used += random.uniform(0.5, 2.0)
            
            # If countdown ends, failure occurs within the next 6h window!
            target_down = 1 if degradation_countdown <= 3 else 0
            if degradation_countdown <= 0:
                in_degradation = False
        else:
            # Normal operational telemetry
            lat = random.uniform(35.0, 110.0)
            pkl = 0.0 if random.random() > 0.03 else random.uniform(0.5, 2.0)
            status = "HEALTHY"
            target_down = 0

        # Append check
        checks_history.append({
            "timestamp": current_time,
            "response_time_ms": lat,
            "packet_loss_percent": pkl,
            "success": True,
            "status": status
        })

        # Keep history bounded
        if len(checks_history) > 150:
            checks_history.pop(0)

        # Extract strictly past features
        features = extract_features_from_history(
            checks=checks_history,
            service_sla={
                "budget_consumption_percent": min(100.0, budget_used),
                "remaining_downtime_minutes": max(0.0, 432.0 - (budget_used * 4.32))
            },
            incidents_24h=1 if in_degradation else 0,
            hours_since_incident=12.0 if in_degradation else 96.0,
            reference_time=current_time
        )

        if features:
            data_rows.append(features)
            labels.append(target_down)

    df_X = pd.DataFrame(data_rows, columns=FEATURE_NAMES)
    df_y = pd.Series(labels, name="target_down_next_6h")
    return df_X, df_y

def prepare_time_series_splits(
    X: pd.DataFrame,
    y: pd.Series,
    train_pct: float = 0.70,
    val_pct: float = 0.15
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Time-aware splitting strictly preserving chronological order.
    Oldest 70% -> Train
    Next 15%   -> Validation
    Newest 15% -> Test
    No random shuffling is allowed!
    """
    n = len(X)
    train_end = int(n * train_pct)
    val_end = int(n * (train_pct + val_pct))

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

    return X_train, y_train, X_val, y_val, X_test, y_test
