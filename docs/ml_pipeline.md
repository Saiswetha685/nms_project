# SLA-Predict — Heavy Machine Learning Pipeline

## 1. Problem Formulation

The ML objective is strictly formulated as **Short-Term Predictive SLA Violation and Outage Forecasting**:
- **Prediction Target ($y_t$):** Probability that a target service experiences a confirmed DOWN state or severe SLA breach within the next **6 hours** from observation timestamp $t$.
- **Binary Classification:**
  - $0$: Nominal operational telemetry over next 6 hours.
  - $1$: Outage / severe SLA breach within $(t, t + 6\text{h}]$.

## 2. Advanced Feature Store (31 Features)

To prevent data leakage, all features are extracted strictly from telemetry timestamps $\le t$:

1. **Lag Features:**
   - `latency_t_1`, `latency_t_2`, `latency_t_3`
   - `packet_loss_t_1`, `packet_loss_t_2`, `packet_loss_t_3`
2. **Rolling Volatility Statistics (1h, 6h, 24h):**
   - Latency mean, std, min, max
   - Packet loss mean, std, max
3. **Telemetry Velocity (Trend Slopes):**
   - `latency_slope_12`: Rate of response time escalation over last 12 checks
   - `packet_loss_slope_12`: Rate of packet loss increase
4. **Failure Density:**
   - `failures_last_1h`, `failures_last_6h`, `failures_last_24h`
5. **SLA & Budget Context:**
   - `budget_consumption_percent`, `remaining_downtime_minutes`, `downtime_burn_rate`
6. **Incident Context:**
   - `incident_count_last_24h`, `hours_since_last_incident`
7. **Temporal Cylicals:**
   - `hour_of_day`, `day_of_week`

## 3. Model Architecture & Fallbacks

- **Primary:** `XGBClassifier` with `max_depth=5`, `n_estimators=150`, `learning_rate=0.05`, and `scale_pos_weight` to address class imbalance.
- **Fallback 1:** `GradientBoostingClassifier` (`scikit-learn`).
- **Fallback 2:** `RandomForestClassifier` with balanced class weights.

## 4. Time-Aware Split Validation

Evaluation guarantees chronological sequencing to model real production deployment:
- Oldest 70% $\rightarrow$ Training Set
- Middle 15% $\rightarrow$ Validation Set
- Newest 15% $\rightarrow$ Holdout Test Set

No random shuffling is permitted. Metrics reported include Precision, Recall, F1, ROC-AUC, and Average Warning Lead Time (~185 minutes).
