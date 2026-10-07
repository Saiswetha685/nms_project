import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

from backend.app.schemas.service import ServiceStatus, ServiceType
from backend.app.monitoring.rules import evaluate_raw_check, update_anti_flapping_state
from backend.app.ml.features import calculate_slope, extract_features_from_history, FEATURE_NAMES
from backend.app.ml.dataset import prepare_time_series_splits
from backend.app.forecasting.holt_winters import exponential_smoothing_forecast
from backend.app.auth.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing_and_jwt():
    raw = "SecureSecret@123"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass", hashed) is False

    token = create_access_token({"sub": "admin@slapredict.io", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "admin@slapredict.io"
    assert payload["role"] == "admin"

def test_deterministic_rules():
    # 1. Healthy HTTP
    st1 = evaluate_raw_check(
        service_type=ServiceType.HTTP,
        success=True,
        response_time_ms=85.0,
        packet_loss_percent=0.0,
        expected_ms=150.0,
        warning_ms=350.0,
        critical_ms=700.0
    )
    assert st1 == ServiceStatus.HEALTHY

    # 2. Warning HTTP
    st2 = evaluate_raw_check(
        service_type=ServiceType.HTTP,
        success=True,
        response_time_ms=220.0,
        packet_loss_percent=0.0,
        expected_ms=150.0,
        warning_ms=350.0,
        critical_ms=700.0
    )
    assert st2 == ServiceStatus.WARNING

    # 3. Critical HTTP
    st3 = evaluate_raw_check(
        service_type=ServiceType.HTTP,
        success=True,
        response_time_ms=500.0,
        packet_loss_percent=0.0,
        expected_ms=150.0,
        warning_ms=350.0,
        critical_ms=700.0
    )
    assert st3 == ServiceStatus.CRITICAL

    # 4. Failed check -> DOWN
    st4 = evaluate_raw_check(
        service_type=ServiceType.HTTP,
        success=False,
        response_time_ms=0.0,
        packet_loss_percent=100.0,
        expected_ms=150.0,
        warning_ms=350.0,
        critical_ms=700.0,
        error="Connection refused"
    )
    assert st4 == ServiceStatus.DOWN

def test_anti_flapping_state_machine():
    # Needs 2 consecutive failures to become DOWN
    current = ServiceStatus.HEALTHY
    st, fails, succs, changed = update_anti_flapping_state(
        current_stored_status=current,
        raw_status=ServiceStatus.DOWN,
        consecutive_failures=0,
        consecutive_successes=5,
        consecutive_failures_down=2,
        consecutive_successes_recovery=2
    )
    # After 1st failure: still HEALTHY (anti-flapping damping)
    assert st == ServiceStatus.HEALTHY
    assert fails == 1
    assert changed is False

    # After 2nd failure: transitions to DOWN
    st2, fails2, succs2, changed2 = update_anti_flapping_state(
        current_stored_status=st,
        raw_status=ServiceStatus.DOWN,
        consecutive_failures=fails,
        consecutive_successes=0,
        consecutive_failures_down=2,
        consecutive_successes_recovery=2
    )
    assert st2 == ServiceStatus.DOWN
    assert fails2 == 2
    assert changed2 is True

    # Needs 2 consecutive successes to recover from DOWN
    st3, fails3, succs3, changed3 = update_anti_flapping_state(
        current_stored_status=ServiceStatus.DOWN,
        raw_status=ServiceStatus.HEALTHY,
        consecutive_failures=2,
        consecutive_successes=0,
        consecutive_failures_down=2,
        consecutive_successes_recovery=2
    )
    assert st3 == ServiceStatus.DOWN
    assert succs3 == 1
    assert changed3 is False

    # 2nd success triggers RECOVERY
    st4, fails4, succs4, changed4 = update_anti_flapping_state(
        current_stored_status=ServiceStatus.DOWN,
        raw_status=ServiceStatus.HEALTHY,
        consecutive_failures=0,
        consecutive_successes=1,
        consecutive_failures_down=2,
        consecutive_successes_recovery=2
    )
    assert st4 == ServiceStatus.HEALTHY
    assert changed4 is True

def test_ml_feature_store_and_leakage():
    now = datetime.now(timezone.utc)
    checks = []
    for i in range(20):
        checks.append({
            "timestamp": now - timedelta(minutes=(20 - i) * 5),
            "response_time_ms": 40.0 + i * 2.0,
            "packet_loss_percent": 0.0,
            "success": True,
            "status": "HEALTHY"
        })

    features = extract_features_from_history(
        checks=checks,
        service_sla={"budget_consumption_percent": 30.0, "remaining_downtime_minutes": 300.0},
        incidents_24h=0,
        hours_since_incident=48.0,
        reference_time=now
    )

    assert features is not None
    assert len(features) == len(FEATURE_NAMES)
    assert features["latency_slope_12"] > 0  # Slope should be positive due to increasing latency
    assert features["budget_consumption_percent"] == 30.0

def test_time_series_chronological_splits():
    df_X = pd.DataFrame(np.random.randn(100, 10))
    df_y = pd.Series(np.random.randint(0, 2, 100))

    X_train, y_train, X_val, y_val, X_test, y_test = prepare_time_series_splits(df_X, df_y)
    assert len(X_train) == 70
    assert len(X_val) == 15
    assert len(X_test) == 15
    # Assure indices are strictly sequential without shuffling
    assert list(X_train.index) == list(range(0, 70))
    assert list(X_val.index) == list(range(70, 85))
    assert list(X_test.index) == list(range(85, 100))

def test_holt_winters_forecast():
    series = [0.0, 0.0, 1.2, 2.5, 3.1, 4.0, 5.2]
    point_fc, lowers, uppers = exponential_smoothing_forecast(series, forecast_steps=12)
    assert len(point_fc) == 12
    assert len(lowers) == 12
    assert len(uppers) == 12
    # Upper bound should be >= point forecast >= lower bound
    for p, l, u in zip(point_fc, lowers, uppers):
        assert u >= p >= l
