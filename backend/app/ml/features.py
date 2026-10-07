import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

FEATURE_NAMES = [
    "latency_t_1", "latency_t_2", "latency_t_3",
    "packet_loss_t_1", "packet_loss_t_2", "packet_loss_t_3",
    "latency_mean_1h", "latency_std_1h", "latency_min_1h", "latency_max_1h",
    "packet_loss_mean_1h", "packet_loss_std_1h", "packet_loss_max_1h",
    "latency_mean_6h", "latency_std_6h", "latency_max_6h",
    "latency_mean_24h", "latency_std_24h", "latency_max_24h",
    "latency_slope_12", "packet_loss_slope_12",
    "failures_last_1h", "failures_last_6h", "failures_last_24h",
    "budget_consumption_percent", "remaining_downtime_minutes", "downtime_burn_rate",
    "incident_count_last_24h", "hours_since_last_incident",
    "hour_of_day", "day_of_week"
]

def calculate_slope(series: List[float]) -> float:
    """Calculates linear slope (velocity) of a sequence of values"""
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    y = np.array(series, dtype=float)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    denominator = np.sum((x - x_mean) ** 2)
    if denominator == 0:
        return 0.0
    slope = np.sum((x - x_mean) * (y - y_mean)) / denominator
    return float(round(slope, 4))

def extract_features_from_history(
    checks: List[Dict[str, Any]],
    service_sla: Dict[str, Any] = None,
    incidents_24h: int = 0,
    hours_since_incident: float = 72.0,
    reference_time: datetime = None
) -> Optional[Dict[str, float]]:
    """
    Extracts time-series features strictly from historical checks prior to reference_time.
    Guarantees NO target leakage.
    Checks must be ordered chronologically ascending.
    """
    if not checks:
        return None

    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    # Filter to checks on or before reference_time
    valid_checks = []
    for c in checks:
        ts = c.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts and ts <= reference_time:
            valid_checks.append((ts, c))

    if not valid_checks:
        return None

    valid_checks.sort(key=lambda x: x[0])
    recent_records = [x[1] for x in valid_checks]

    latencies = [float(r.get("response_time_ms", 0.0)) for r in recent_records]
    packet_losses = [float(r.get("packet_loss_percent", 0.0)) for r in recent_records]

    # Lag features (t-1, t-2, t-3)
    l1 = latencies[-1] if len(latencies) >= 1 else 0.0
    l2 = latencies[-2] if len(latencies) >= 2 else l1
    l3 = latencies[-3] if len(latencies) >= 3 else l2

    p1 = packet_losses[-1] if len(packet_losses) >= 1 else 0.0
    p2 = packet_losses[-2] if len(packet_losses) >= 2 else p1
    p3 = packet_losses[-3] if len(packet_losses) >= 3 else p2

    # Rolling window partitions (1h, 6h, 24h)
    ref_ts = valid_checks[-1][0]
    checks_1h = [r for ts, r in valid_checks if (ref_ts - ts).total_seconds() <= 3600]
    checks_6h = [r for ts, r in valid_checks if (ref_ts - ts).total_seconds() <= 21600]
    checks_24h = [r for ts, r in valid_checks if (ref_ts - ts).total_seconds() <= 86400]

    lat_1h = [float(r.get("response_time_ms", 0.0)) for r in checks_1h] or [l1]
    pkl_1h = [float(r.get("packet_loss_percent", 0.0)) for r in checks_1h] or [p1]

    lat_6h = [float(r.get("response_time_ms", 0.0)) for r in checks_6h] or lat_1h
    lat_24h = [float(r.get("response_time_ms", 0.0)) for r in checks_24h] or lat_6h

    # Slopes over last 12 checks
    lat_12 = latencies[-12:] if len(latencies) >= 12 else latencies
    pkl_12 = packet_losses[-12:] if len(packet_losses) >= 12 else packet_losses
    slope_lat = calculate_slope(lat_12)
    slope_pkl = calculate_slope(pkl_12)

    # Failure counts
    fail_1h = sum(1 for r in checks_1h if not r.get("success", True) or r.get("status") == "DOWN")
    fail_6h = sum(1 for r in checks_6h if not r.get("success", True) or r.get("status") == "DOWN")
    fail_24h = sum(1 for r in checks_24h if not r.get("success", True) or r.get("status") == "DOWN")

    # SLA and budget context
    budget_pct = 0.0
    rem_downtime = 432.0
    burn_rate = 0.0
    if service_sla:
        budget_pct = float(service_sla.get("budget_consumption_percent", 0.0))
        rem_downtime = float(service_sla.get("remaining_downtime_minutes", 432.0))
        burn_rate = round(float(fail_1h) * 0.5, 2)  # minutes per hour burn

    hour = ref_ts.hour
    day = ref_ts.weekday()

    return {
        "latency_t_1": float(round(l1, 2)),
        "latency_t_2": float(round(l2, 2)),
        "latency_t_3": float(round(l3, 2)),
        "packet_loss_t_1": float(round(p1, 2)),
        "packet_loss_t_2": float(round(p2, 2)),
        "packet_loss_t_3": float(round(p3, 2)),
        "latency_mean_1h": float(round(np.mean(lat_1h), 2)),
        "latency_std_1h": float(round(np.std(lat_1h), 2)),
        "latency_min_1h": float(round(np.min(lat_1h), 2)),
        "latency_max_1h": float(round(np.max(lat_1h), 2)),
        "packet_loss_mean_1h": float(round(np.mean(pkl_1h), 2)),
        "packet_loss_std_1h": float(round(np.std(pkl_1h), 2)),
        "packet_loss_max_1h": float(round(np.max(pkl_1h), 2)),
        "latency_mean_6h": float(round(np.mean(lat_6h), 2)),
        "latency_std_6h": float(round(np.std(lat_6h), 2)),
        "latency_max_6h": float(round(np.max(lat_6h), 2)),
        "latency_mean_24h": float(round(np.mean(lat_24h), 2)),
        "latency_std_24h": float(round(np.std(lat_24h), 2)),
        "latency_max_24h": float(round(np.max(lat_24h), 2)),
        "latency_slope_12": float(slope_lat),
        "packet_loss_slope_12": float(slope_pkl),
        "failures_last_1h": float(fail_1h),
        "failures_last_6h": float(fail_6h),
        "failures_last_24h": float(fail_24h),
        "budget_consumption_percent": float(round(budget_pct, 2)),
        "remaining_downtime_minutes": float(round(rem_downtime, 2)),
        "downtime_burn_rate": float(burn_rate),
        "incident_count_last_24h": float(incidents_24h),
        "hours_since_last_incident": float(min(168.0, hours_since_incident)),
        "hour_of_day": float(hour),
        "day_of_week": float(day)
    }
