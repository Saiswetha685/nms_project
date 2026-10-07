# SLA-Predict — Antigravity Master Build Prompt

## Project Identity

**Project Title:** SLA-Predict: Intelligent Network Service Monitoring and Predictive SLA Violation Detection System

**Project Type:** Web-based Network Management System (NMS) with Advanced Predictive Analytics and Machine Learning.

Build a complete, functional, production-style college project — **not a UI prototype, mockup, or basic CRUD wrapper**.

The system continuously monitors important network services, calculates deterministic health and SLA compliance, manages incidents and alerts, and adds an advanced ML layer for proactive SLA-risk assessment and short-term failure prediction.

---

## 1. Core Objective

The system must answer:

1. Is this service available now?
2. Is it responding within acceptable limits?
3. Is it meeting its SLA?
4. Is it statistically trending toward an upcoming SLA violation or DOWN event?

The deterministic monitoring/SLA engine is the **source of truth**. Machine learning and forecasting are **advisory intelligence only** and must never silently change actual service status, SLA verdict, incident state, or downtime calculation.

---

## 2. High-Level Architecture

```text
Network Targets
      |
      v
Async Monitoring Engine
      |
      +-- HTTP / HTTPS
      +-- ICMP / Ping
      +-- TCP
      +-- DNS
      |
      v
Rule-Based Evaluation
      |
      +-- HEALTHY
      +-- WARNING
      +-- CRITICAL
      +-- DOWN
      |
      v
SLA Calculator
      |
      +-- Availability %
      +-- Downtime
      +-- SLA Compliance
      +-- Remaining Downtime Budget
      |
      +-----------------------------+
      v                             v
Rule-Based SLA Risk          Heavy ML Layer
Baseline                     |
      |                      +-- Feature Store
      |                      +-- Lag Features
      |                      +-- Rolling Statistics
      |                      +-- Trend / Velocity
      |                      +-- Failure Density
      |                      +-- XGBoost / Gradient Boosting
      |                      +-- Hyperparameter Optimization
      |                      +-- Probability Scoring
      |                             |
      +--------------+--------------+
                     v
             Combined Risk Assessment
                     |
             +-------+-------+
             v               v
      Explainable Risk   Statistical Forecast
                         (Holt-Winters)
             |               |
             +-------+-------+
                     v
              Claude Explanation
                     |
                     v
              Proactive Alerting
                     |
                     v
               FastAPI Backend
                     |
              REST + WebSocket
                     |
                     v
               React Dashboard
```

---

## 3. Technology Stack

### Frontend
- React
- Vite
- Tailwind CSS
- Recharts
- Axios
- Lucide React

### Backend
- Python
- FastAPI
- Pydantic
- JWT authentication
- WebSockets

### Database
- MongoDB
- Motor for async access
- PyMongo where appropriate

### Monitoring
- httpx
- icmplib
- asyncio
- dnspython
- APScheduler

### Machine Learning
- pandas
- numpy
- scikit-learn
- XGBoost
- LightGBM optional
- joblib
- statsmodels

### LLM
- Anthropic Claude API, server-side only

### Reports / Utilities
- python-dotenv
- ReportLab
- CSV

---

## 4. Scope Boundaries

### Must include
- HTTP/HTTPS availability monitoring
- Ping/packet-loss monitoring
- TCP connectivity checks
- DNS checks
- Response-time monitoring
- SLA compliance
- Downtime-budget calculation
- Incident management
- Alert management
- Anti-flapping
- Rule-based SLA risk scoring
- Advanced ML failure prediction
- SLA downtime-budget exhaustion forecasting
- Explainable ML results
- Claude-generated explanations
- Historical charts
- CSV/PDF reports
- Demo/simulation mode
- REST APIs
- WebSocket live updates
- Authentication/RBAC

### Must not become
- Generic anomaly detection
- DDoS detection
- Network topology discovery
- Bandwidth monitoring/optimization
- Network configuration management
- Generic capacity forecasting
- Deep-learning/LSTM network prediction
- ML-controlled service status
- ML-controlled SLA verdict

The ML problem is specifically **predictive SLA violation / short-term DOWN risk**.

---

## 5. Roles and Authentication

### Admin
Can create/edit/delete services, configure SLA and thresholds, manage users, view incidents/alerts, train ML models, run simulations, and generate reports.

### Operator
Can view the dashboard/services, acknowledge incidents and alerts, view SLA and predictive risk, and generate reports.

Implement:
- Login
- JWT access token
- Password hashing
- Protected routes
- Role-based authorization
- Logout
- Current-user endpoint
- Persistent authentication state

Never store plain-text passwords.

---

## 6. Service Registry

Each monitored service should contain:

```text
service_id
name
description
type
target
port
url
enabled
check_interval_seconds
timeout_seconds
expected_response_ms
warning_response_ms
critical_response_ms
sla_target_percent
sla_window_days
count_degraded_as_downtime
consecutive_failures_down
consecutive_successes_recovery
notification_enabled
created_at
updated_at
```

Supported types:
- HTTP
- HTTPS
- PING
- TCP
- DNS

Seed examples:
- College Website
- Student Portal
- DNS Service
- Email Service
- Library System
- Database Service

---

## 7. Async Monitoring Engine

Use asynchronous monitoring so multiple services can be checked without blocking the backend.

Use:
- asyncio
- httpx
- icmplib
- dnspython
- TCP sockets
- APScheduler

Every check must produce a normalized record:

```json
{
  "service_id": "svc_001",
  "timestamp": "2026-10-06T10:30:00Z",
  "status": "HEALTHY",
  "response_time_ms": 120,
  "packet_loss_percent": 0,
  "success": true,
  "error": null,
  "check_type": "HTTP"
}
```

---

## 8. Monitoring Rules

### HTTP/HTTPS
Track response time, HTTP status, timeout, connection errors, and request success.

Suggested interpretation:
- 2xx = successful
- 3xx = configurable
- 4xx = unhealthy/error
- 5xx = failure
- timeout/connection failure = DOWN

### Ping
Track latency, packet loss, timeout, and success/failure.

Suggested defaults:
```text
0–2% packet loss   = HEALTHY
>2–10%             = WARNING
>10%               = CRITICAL
100%               = DOWN
```

### TCP
Track connection success, connection time, timeout, and error.

### DNS
Track resolution success, lookup response time, returned records where useful, and timeout/error.

---

## 9. Deterministic Status Evaluation

The rule engine is authoritative.

For response-time services:

```text
No response / timeout
        -> DOWN

response_time <= expected threshold
        -> HEALTHY

expected threshold < response_time <= 2x threshold
        -> WARNING

response_time > 2x threshold
        -> CRITICAL
```

Make thresholds configurable.

### Anti-flapping
Default:
```text
2 consecutive failures -> DOWN
2 consecutive successes -> RECOVERY
```

Store current status, previous status, consecutive failure count, and consecutive success count.

---

## 10. SLA Calculation

For a configured SLA such as 99% over 30 days:

```text
Total minutes = 30 x 24 x 60 = 43,200
Allowed downtime = 43,200 x (1 - 0.99) = 432 minutes
```

Availability:

```text
Availability % = Available time / Total observed time x 100
```

Default:
- HEALTHY = available
- WARNING = available
- CRITICAL = available
- DOWN = unavailable

Support `count_degraded_as_downtime` configuration.

SLA states:
```text
COMPLIANT
AT_RISK
VIOLATED
```

Important: AT_RISK is predictive; VIOLATED is based on the actual deterministic SLA calculation.

---

## 11. Downtime Budget

Calculate:

```text
total_window_minutes
allowed_downtime_minutes
used_downtime_minutes
remaining_downtime_minutes
budget_consumption_percent
```

Example:
```text
Allowed = 432 minutes
Used = 300 minutes
Remaining = 132 minutes
Budget consumption = 69.44%
```

---

## 12. Rule-Based SLA Risk Baseline

Create a transparent 0–100 risk score.

Suggested weights:
```text
Budget pressure      40%
Failure burn rate    30%
Downtime trend       15%
Latency degradation  15%
```

Risk levels:
```text
0–24   LOW
25–49  MEDIUM
50–74  HIGH
75–100 CRITICAL
```

Show the component scores.

### Guardrails
```text
budget >= 75% -> minimum risk 50
budget >= 90% -> minimum risk 75
budget > 100% -> SLA VIOLATED and minimum risk 90
```

### Hysteresis
Enter high-risk state at `risk >= 50`; leave it below `40`.

Default alert cooldown: `60 minutes`.

---

## 13. Heavy Machine Learning Pipeline

Use a substantially stronger ML pipeline than a basic linear model.

Preferred:
```text
XGBClassifier
```

Fallback:
```text
GradientBoostingClassifier
```

Additional fallback:
```text
RandomForestClassifier
```

The system must gracefully fall back if an optional ML package is unavailable.

### Prediction target
Predict the probability that a service experiences a confirmed DOWN state or severe SLA breach within the next **6 hours**.

```text
0 = no event in next 6h
1 = confirmed DOWN/severe SLA breach in next 6h
```

Never use future information in features.

---

## 14. Advanced Feature Engineering

Create a reusable feature store.

### Lag features
```text
latency_t-1
latency_t-2
latency_t-3
packet_loss_t-1
packet_loss_t-2
packet_loss_t-3
```

### Rolling statistics
For 1h, 6h, and 24h windows:
- latency mean
- latency std
- latency min
- latency max
- packet-loss mean
- packet-loss std
- packet-loss max

### Trend/velocity
- latency slope over last 12 checks
- packet-loss slope
- downtime slope

### Failure density
- failures_last_1h
- failures_last_6h
- failures_last_24h

### SLA pressure
- budget_consumption_percent
- remaining_downtime_minutes
- downtime_burn_rate

### Incident context
- time_since_last_incident
- incident_count_last_24h
- recent_recovery_count

### Temporal features
- hour_of_day
- day_of_week

Do not use future values.

---

## 15. ML Training and Evaluation

Starting XGBoost configuration:
```text
max_depth = 5
n_estimators = 150
learning_rate = 0.05
```

Allow lightweight hyperparameter optimization with GridSearchCV or RandomizedSearchCV when enough data exists.

Possible tuned parameters:
- max_depth
- n_estimators
- learning_rate
- subsample
- colsample_bytree
- min_child_weight
- gamma

Handle imbalance with `scale_pos_weight` for XGBoost or `class_weight="balanced"` for sklearn fallbacks.

Do not rely on accuracy alone.

Metrics:
- Precision
- Recall
- F1
- ROC-AUC
- Confusion Matrix
- Average Warning Lead Time

Prefer time-aware splits, for example:
```text
Oldest 70% -> Train
Next 15%   -> Validation
Newest 15% -> Test
```

Do not randomly shuffle time-series data for final evaluation.

---

## 16. Historical Replay

Implement historical evaluation comparing:

```text
Rule-Based Risk Baseline
vs
Heavy ML Risk Model
```

Report Precision, Recall, F1, ROC-AUC, and average warning lead time.

Seed/simulated data is suitable for demonstration but must not be presented as equivalent to real-world validation.

---

## 17. Model Registry

Store:

```text
model_id
model_type
version
training_start
training_end
training_rows
feature_list
hyperparameters
metrics
model_path
created_at
```

Serialize models with joblib.

Provide nightly retraining and an admin endpoint/button:

```text
POST /ml/train
```

If there is insufficient data, set ML status to `NOT_READY` and fall back to rule-based risk.

---

## 18. Explainability

Use SHAP where available; otherwise use model feature importance.

Example:

> High SLA risk is mainly caused by rising latency volatility and increasing packet loss over the last hour, combined with high downtime-budget consumption.

Never show only an unexplained probability.

Example prediction:

```json
{
  "service_id": "svc_001",
  "prediction_time": "2026-10-06T12:00:00Z",
  "probability_down_next_6h": 0.78,
  "risk_level": "HIGH",
  "model_version": "xgb-v3",
  "top_features": [
    {"feature": "rolling_packet_loss_1h", "importance": 0.31},
    {"feature": "latency_slope_12_checks", "importance": 0.24}
  ]
}
```

---

## 19. Statistical SLA Forecasting

Use Holt-Winters / exponential smoothing through statsmodels where appropriate.

Forecast when the remaining SLA downtime budget may be exhausted if the current downtime trend continues.

Return:
- estimated exhaustion time
- lower confidence bound
- upper confidence bound

Present this as an estimate, never a guarantee.

This is SLA downtime-budget forecasting, not generic capacity forecasting.

---

## 20. Combined Risk

Combine transparently:

```text
Rule-Based Risk
+
ML DOWN Probability
+
SLA Budget Forecast Pressure
```

Use a configurable weighted combination.

ML must never overwrite deterministic status/SLA.

---

## 21. Claude Integration

Claude is used only for explanations and reports.

Claude may receive already-calculated:
- service status
- SLA percentage
- SLA target
- downtime budget
- budget consumption
- risk score
- ML probability
- important features
- forecast ETA
- recent incidents

Claude must NOT:
- decide service status
- calculate SLA
- change SLA state
- decide whether an incident exists
- modify risk values
- execute monitoring actions

If Claude is unavailable, use deterministic template explanations.

Never expose the Claude API key to the frontend.

---

## 22. Incident Management

Incident fields:

```text
incident_id
service_id
started_at
detected_at
ended_at
duration
severity
status
root_cause
description
acknowledged_by
acknowledged_at
resolved_at
```

States:
```text
OPEN
ACKNOWLEDGED
RESOLVED
```

Calculate MTTD, MTTR, duration, and incident count.

---

## 23. Alert Management

Support:
- in-app alerts
- email alerts
- optional webhook

Triggers:
- confirmed DOWN
- recovery
- SLA violation
- high SLA risk
- critical ML prediction
- budget exhaustion risk

Use state-change logic, deduplication, acknowledgement, and cooldown. Do not alert on every failed check.

---

## 24. Database Collections

### users
```text
_id, name, email, password_hash, role, created_at
```

### services
```text
_id, name, type, target, port, url, enabled, check_interval,
timeout, thresholds, sla_config, risk_config, current_state,
created_at, updated_at
```

### checks
```text
_id, service_id, timestamp, check_type, success, status,
response_time_ms, packet_loss_percent, error
```

### incidents
```text
_id, service_id, started_at, ended_at, duration, severity,
status, description
```

### alerts
```text
_id, service_id, type, severity, message, created_at,
acknowledged, acknowledged_by
```

### sla_daily
```text
_id, service_id, date, available_minutes, downtime_minutes,
availability_percent
```

### audit_logs
```text
_id, user_id, action, resource, timestamp, details
```

### sla_risk_snapshots
```text
_id, service_id, timestamp, rule_risk, budget_risk, burn_risk,
trend_risk, latency_risk, ml_probability, combined_risk, risk_level
```

### ml_models
```text
_id, model_type, version, training_start, training_end,
feature_list, hyperparameters, metrics, model_path, created_at
```

### risk_predictions
```text
_id, service_id, timestamp, model_version,
probability_down_next_6h, risk_level, top_features, forecast
```

---

## 25. Backend Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth/
│   ├── models/
│   ├── schemas/
│   ├── api/
│   ├── monitoring/
│   ├── sla/
│   ├── incidents/
│   ├── alerts/
│   ├── risk/
│   ├── ml/
│   ├── forecasting/
│   ├── llm/
│   ├── websocket/
│   └── reports/
├── ml_models/
├── tests/
├── requirements.txt
└── .env.example
```

ML module:
```text
backend/app/ml/
├── features.py
├── dataset.py
├── train.py
├── predict.py
├── evaluate.py
├── explain.py
├── model_registry.py
└── preprocessing.py
```

Forecasting:
```text
backend/app/forecasting/
├── budget_forecast.py
└── holt_winters.py
```

LLM:
```text
backend/app/llm/
├── claude_client.py
└── explanation.py
```

---

## 26. REST API

Implement at least:

### Auth
```text
POST /auth/login
GET /auth/me
```

### Services
```text
GET /services
POST /services
GET /services/{id}
PUT /services/{id}
DELETE /services/{id}
```

### Monitoring
```text
GET /services/{id}/checks
GET /services/{id}/status
POST /services/{id}/check
```

### SLA
```text
GET /services/{id}/sla
GET /services/{id}/sla/history
GET /sla/overview
```

### Incidents
```text
GET /incidents
GET /incidents/{id}
POST /incidents/{id}/acknowledge
POST /incidents/{id}/resolve
```

### Alerts
```text
GET /alerts
POST /alerts/{id}/acknowledge
```

### SLA Risk
```text
GET /services/{id}/sla-risk
GET /services/{id}/sla-risk/history
GET /sla-risk/overview
PUT /services/{id}/sla-risk/config
```

### ML
```text
GET /services/{id}/ml-risk
GET /ml/models
POST /ml/train
GET /ml/evaluation
```

### Forecast
```text
GET /services/{id}/forecast
```

### Reports
```text
GET /reports/sla
GET /reports/availability
GET /reports/incidents
GET /reports/executive-summary
GET /reports/export/csv
GET /reports/export/pdf
```

### Demo
```text
POST /demo/sla-risk/stage/{stage}
```

### WebSocket
```text
/ws/live
```

Broadcast status changes, incidents, alerts, SLA updates, risk updates, and ML predictions.

---

## 27. Frontend Pages

Implement:

1. Login
2. Dashboard
3. Services
4. Add Service
5. Edit Service
6. Service Detail
7. Incidents
8. Alerts
9. SLA Compliance
10. Reports
11. Settings
12. ML / Risk Analytics

---

## 28. Dashboard

Summary cards:
```text
Total Services
Healthy
Warning
Critical
Down
SLA Violations
High-Risk Services
Open Incidents
```

Service table:
```text
Service | Type | Status | Response Time | Availability | SLA | Risk | ML Probability | Last Check
```

Use Recharts for:
- availability trend
- response-time trend
- downtime trend
- risk trend
- SLA budget consumption

---

## 29. Service Detail

Show:

### Current Status
HEALTHY / WARNING / CRITICAL / DOWN

### SLA
- Current Availability
- SLA Target
- Downtime Used
- Downtime Remaining
- Compliance State

### Performance
- Minimum latency
- Average latency
- Maximum latency
- P95 latency
- Packet loss

### Predictive Risk
- Rule Risk
- ML Probability
- Combined Risk
- Top Risk Factors
- Forecast
- Claude Explanation

### History
Charts for latency, packet loss, status, SLA, and risk.

---

## 30. Reports

Generate:

### SLA Compliance Report
Service, target SLA, actual SLA, downtime, budget, compliance state.

### Availability Report
Total checks, successful checks, failed checks, uptime, downtime.

### Response Time Report
Minimum, average, maximum, P95.

### Incident Report
Incident count, duration, MTTD, MTTR, severity.

### Predictive Risk Report
Rule risk, ML probability, risk trend, forecast, warning lead time.

### Executive Summary
Current service health, SLA violations, high-risk services, major incidents, predictive risk, attention areas.

Export CSV and PDF.

---

## 31. Demo / Simulation

Create a controlled simulation mode with:

```text
Stage 1 -> NORMAL
Stage 2 -> LATENCY DEGRADATION
Stage 3 -> PACKET LOSS / FAILURES
Stage 4 -> HIGH SLA RISK
Stage 5 -> DOWN / SLA VIOLATION
Stage 6 -> RECOVERY
```

Demonstration flow:

```text
NORMAL
  -> latency increases
  -> packet loss increases
  -> rule risk increases
  -> ML probability increases
  -> proactive alert
  -> service goes DOWN
  -> SLA budget decreases
  -> SLA violation
  -> recovery
```

Make this visually obvious in the dashboard.

---

## 32. Seed Data

Seed realistic services and enough historical monitoring data for charts and rule/SLA demonstration.

ML training data must be clearly identified as demo/simulated where applicable. Do not present synthetic data as real-world validation.

---

## 33. ML Data Sufficiency and Leakage Prevention

If insufficient historical failure data exists:

```text
ML status = NOT_READY
```

Fall back to rule-based risk.

Before training:
- sort by timestamp
- generate features only from historical values
- create the future 6-hour target separately
- remove rows without known future target
- use time-aware train/validation/test splits

Absolutely prevent target leakage.

---

## 34. Engineering Requirements

The application must:
- start with documented commands
- contain `.env.example`
- validate configuration
- handle MongoDB failures
- handle monitoring exceptions/timeouts
- handle invalid URLs
- handle unavailable DNS
- handle missing ML dependencies
- handle Claude API failure
- log important backend events
- avoid blocking the event loop
- use environment variables for secrets
- never expose secrets to frontend
- use correct HTTP status codes
- validate API inputs
- prevent unauthorized access
- use reusable modules/classes
- avoid duplicated logic

---

## 35. Environment Variables

Create:

```text
MONGODB_URI=
DATABASE_NAME=
JWT_SECRET=
JWT_EXPIRE_MINUTES=
ANTHROPIC_API_KEY=
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
FRONTEND_URL=
```

Never commit actual secrets.

---

## 36. Testing

Test:

### Monitoring
- HTTP success
- HTTP timeout
- HTTP failure
- DNS failure
- TCP failure
- Ping loss

### Status Rules
- healthy threshold
- warning threshold
- critical threshold
- down state

### Anti-Flapping
- repeated failures
- repeated successes
- recovery

### SLA
- availability
- downtime
- budget
- SLA violation

### Risk
- rule score
- risk levels
- guardrails
- hysteresis

### ML
- feature generation
- leakage prevention
- training
- prediction
- model loading
- insufficient-data fallback

### Forecast
- forecast creation
- missing data
- confidence intervals

### API
- authentication
- RBAC
- services
- incidents
- alerts
- risk
- reports

---

## 37. Build Order

### Phase 1 — Core Infrastructure
FastAPI, React/Vite, Tailwind, MongoDB, authentication, configuration.

### Phase 2 — Service Registry
Service CRUD, SLA configuration, thresholds.

### Phase 3 — Monitoring
HTTP, HTTPS, Ping, TCP, DNS, async scheduling, persistence.

### Phase 4 — Deterministic Rules
Status evaluation, anti-flapping, incidents, alerts.

### Phase 5 — SLA Engine
Availability, downtime, budget, compliance, reports.

### Phase 6 — Rule-Based Risk
Budget pressure, burn rate, trend, latency degradation, score, hysteresis.

### Phase 7 — Heavy ML
Feature store, lag features, rolling statistics, trends, failure density, XGBoost, fallbacks, tuning, evaluation, registry, predictions.

### Phase 8 — Forecasting
Holt-Winters, budget exhaustion ETA, confidence intervals.

### Phase 9 — Claude
Risk explanation, incident summary, executive summary.

### Phase 10 — Frontend Analytics
Risk cards, ML probability, forecast, explainability, charts.

### Phase 11 — Reports
CSV, PDF, executive summary.

### Phase 12 — Simulation
Normal, degradation, failures, high risk, outage, recovery.

### Phase 13 — Testing and Polish
Integration tests, UI polish, error handling, documentation, demo preparation.

---

## 38. Documentation

Create:

```text
README.md
docs/
├── architecture.md
├── api.md
├── ml_pipeline.md
├── sla_calculation.md
└── demo.md
```

README must document:
- project overview
- architecture
- prerequisites
- MongoDB setup
- backend setup
- frontend setup
- environment variables
- start commands
- seed data
- monitoring startup
- ML training
- tests
- demo simulation
- API overview
- ML methodology
- risk calculation
- SLA calculation
- limitations

---

## 39. UI Quality

Make the UI look like a real modern monitoring product.

Use:
- clean cards
- responsive layouts
- status badges
- risk indicators
- useful charts
- readable tables
- loading states
- empty states
- error states
- confirmation dialogs
- toast notifications

Prioritize clarity and operational usefulness over decoration.

---

## 40. Research Contribution

Use this contribution statement:

> **“An explainable hybrid SLA-risk monitoring framework that extends conventional network service availability and SLA-compliance monitoring with rule-based risk scoring, advanced machine-learning-based short-term failure probability, statistical SLA-budget exhaustion estimation, and proactive alerts while preserving deterministic and auditable SLA decisions.”**

The novelty is the combination of:

```text
Traditional Monitoring
        +
Deterministic SLA Calculation
        +
Explainable Risk Baseline
        +
Advanced ML Prediction
        +
SLA Budget Forecasting
        +
Proactive Alerts
        +
LLM-Based Explanation
```

---

## 41. Final Acceptance Criteria

The project is complete only when:

- Users can log in.
- Admin can create services.
- Services are monitored asynchronously.
- HTTP/HTTPS/Ping/TCP/DNS checks work.
- Check results are stored.
- Service status is deterministic.
- Anti-flapping works.
- Incidents are created/resolved.
- Alerts are generated and deduplicated.
- SLA is calculated correctly.
- Downtime budget is calculated correctly.
- Rule-based risk is calculated.
- Risk history is stored.
- ML features are generated without leakage.
- Heavy ML can train when enough data exists.
- ML predictions are stored.
- Model versions are stored.
- Evaluation metrics are displayed.
- Rule baseline can be compared with ML.
- Forecast is generated when sufficient data exists.
- Claude can explain calculated risk.
- Claude failure does not break the app.
- Dashboard updates through WebSockets.
- Reports can be exported.
- Simulation demonstrates NORMAL -> RISK -> VIOLATION -> RECOVERY.
- Actual SLA status is clearly separated from predicted risk.
- Clean setup and documented commands work.

---

## 42. Antigravity Build Instructions

You are the coding/build agent.

Do not merely generate static UI screens. Build the actual end-to-end application.

Before implementation:
1. Inspect the repository.
2. Determine existing files.
3. Preserve useful existing work.
4. Create missing folders/modules.
5. Avoid duplicate functionality.

During implementation:
1. Build backend and frontend incrementally.
2. Keep the app runnable after each major phase.
3. Use real MongoDB persistence.
4. Use real asynchronous monitoring.
5. Use real APIs.
6. Implement deterministic rules before ML.
7. Implement ML only after monitoring/SLA data structures exist.
8. Never hard-code dashboard metrics that should come from the backend.
9. Use WebSockets for live state changes.
10. Keep secrets server-side.

When optional dependencies such as XGBoost, SHAP, or Claude are unavailable:
- do not crash the whole application;
- use the documented fallback;
- show the feature as unavailable/not ready.

---

## 43. Final System Principle

The architecture must clearly separate:

```text
DETERMINISTIC DECISION LAYER
```

from:

```text
PREDICTIVE INTELLIGENCE LAYER
```

The deterministic layer decides:
- actual service status
- actual availability
- SLA compliance
- actual incidents
- actual downtime

The predictive layer estimates:
- future DOWN probability
- future SLA risk
- budget exhaustion
- risk explanations

**Do not weaken this project into a simple CRUD dashboard.**

Final flow:

```text
LIVE MONITORING
      ↓
DETERMINISTIC HEALTH
      ↓
SLA CALCULATION
      ↓
DOWNTIME BUDGET
      ↓
RULE-BASED RISK
      ↓
HEAVY ML PREDICTION
      ↓
STATISTICAL FORECAST
      ↓
EXPLAINABILITY
      ↓
PROACTIVE ALERT
      ↓
INCIDENT / SLA MANAGEMENT
      ↓
REPORTING
```

The deterministic monitoring/SLA layer remains authoritative. Advanced ML and forecasting provide **early warning and decision support**, not uncontrolled automated decisions.
