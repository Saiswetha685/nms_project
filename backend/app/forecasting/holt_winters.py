import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("sla_predict.forecasting")

def exponential_smoothing_forecast(
    series: List[float],
    forecast_steps: int = 24,
    alpha: float = 0.3,
    beta: float = 0.1
) -> Tuple[List[float], List[float], List[float]]:
    """
    Double exponential smoothing (Holt's linear trend method)
    with statsmodels Holt-Winters fallback.
    Returns:
        (point_forecasts, lower_bounds, upper_bounds)
    """
    if len(series) < 3:
        # Default flat projection if insufficient points
        val = series[-1] if series else 0.0
        return [val] * forecast_steps, [max(0.0, val * 0.8)] * forecast_steps, [val * 1.2] * forecast_steps

    # Attempt statsmodels ExponentialSmoothing
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,
            initialization_method="estimated"
        ).fit()
        forecast = list(model.forecast(forecast_steps))
        # Compute empirical standard error from residuals
        residuals = np.array(model.resid)
        std_err = float(np.std(residuals)) if len(residuals) > 0 else 0.5
        
        lowers = [float(max(0.0, f - 1.96 * std_err * np.sqrt(step + 1))) for step, f in enumerate(forecast)]
        uppers = [float(f + 1.96 * std_err * np.sqrt(step + 1)) for step, f in enumerate(forecast)]
        return [float(max(0.0, f)) for f in forecast], lowers, uppers
    except Exception as e:
        logger.debug("Statsmodels Holt-Winters fit fallback triggered: %s", e)

    # Pure Python Double Exponential Smoothing fallback
    level = series[0]
    trend = series[1] - series[0]
    
    for val in series[1:]:
        last_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend

    forecasts = []
    lowers = []
    uppers = []
    
    # Estimate noise variance
    variance = float(np.var(series)) if len(series) > 1 else 0.5
    std_dev = np.sqrt(variance)

    for h in range(1, forecast_steps + 1):
        y_hat = max(0.0, level + (h * trend))
        margin = 1.96 * std_dev * np.sqrt(h)
        forecasts.append(round(y_hat, 2))
        lowers.append(round(max(0.0, y_hat - margin), 2))
        uppers.append(round(y_hat + margin, 2))

    return forecasts, lowers, uppers
