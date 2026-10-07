# SLA-Predict: Intelligent Network Service Monitoring & Predictive SLA Violation Detection System

> **Academic & Research Contribution Statement:**  
> *“An explainable hybrid SLA-risk monitoring framework that extends conventional network service availability and SLA-compliance monitoring with rule-based risk scoring, advanced machine-learning-based short-term failure probability, statistical SLA-budget exhaustion estimation, and proactive alerts while preserving deterministic and auditable SLA decisions.”*

---

## 🚀 Key Features

- **Authoritative Deterministic Health Layer:**
  - Multi-protocol asynchronous monitoring (HTTP, HTTPS, ICMP Ping, TCP Socket, DNS Lookup).
  - Anti-flapping state machine (configurable consecutive failures for DOWN and consecutive successes for RECOVERY).
  - Authoritative SLA availability calculation and real-time Downtime Budget tracking.
- **Predictive Intelligence Layer:**
  - **Heavy ML Pipeline:** XGBoost / Gradient Boosting ensemble predicting confirmed DOWN state within the next **6 hours**.
  - **Time-Series Feature Store:** 31 lag, rolling volatility (1h, 6h, 24h), trend slopes, failure density, and SLA burn rate features strictly free of target leakage.
  - **Statistical Forecasting:** Holt-Winters double exponential smoothing projecting remaining downtime budget exhaustion ETA with 95% confidence intervals.
  - **Explainability:** Feature importance attribution and server-side Claude AI root cause synthesis.
- **Full Operational NOC Workflow:**
  - Incident management with automated opening, MTTR/MTTD analytics, and operator acknowledgment/resolution.
  - Deduplicated alerting with state cooldowns and email dispatch.
  - Executive audit reports with instant CSV and ReportLab PDF downloads.
  - Controlled 6-stage interactive demonstration console with live WebSocket telemetry updates.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS v4, Recharts, Axios, Lucide React |
| **Backend** | Python 3.14 / 3.10+, FastAPI, Pydantic, Motor (Async MongoDB), PyMongo |
| **ML & Stats** | XGBoost, scikit-learn, statsmodels, pandas, numpy, joblib |
| **Monitoring** | httpx, icmplib, dnspython, asyncio, APScheduler |
| **Database** | MongoDB Server |
| **AI Copilot** | Anthropic Claude API (server-side with deterministic fallback) |
| **Exports** | ReportLab (PDF), RFC 4180 CSV |

---

## 📋 Default Credentials

The database auto-seeds these accounts on first startup:

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Admin** | `admin@slapredict.io` | `Admin@123` | Full control: service CRUD, model training, config |
| **Operator** | `operator@slapredict.io` | `Operator@123` | Read-only telemetry, ticket acknowledge & resolve |

*(The login screen also provides 1-click credential autofill buttons for rapid demonstration!)*

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- **Python:** 3.10 or higher (Python 3.14 tested & verified)
- **Node.js & npm:** Node 18+ (Node 26+ tested)
- **MongoDB Server:** Running locally on port `27017`

### 2. Backend Setup
From the project root:

```bash
# 1. Install Python dependencies
python -m pip install -r backend/requirements.txt

# 2. Configure environment (already preset in backend/.env)
# MONGODB_URI=mongodb://localhost:27017
# DATABASE_NAME=sla_predict_db

# 3. Start FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Frontend Setup
In a new terminal:

```bash
cd frontend

# Dependencies are already installed; to run dev server:
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Running Automated Tests

Run the complete backend test suite covering security, status rules, anti-flapping, ML feature stores, and Holt-Winters forecasting:

```bash
python -m pytest backend/tests/test_nms.py -v
```

---

## 🎮 Interactive Simulation Walkthrough

1. Log in as **Admin** (`admin@slapredict.io`).
2. Navigate to **Scenario Simulation** from the sidebar.
3. Click through the 6 progressive stages:
   - **Stage 1 (Normal):** Nominal latency (~45ms), healthy baseline.
   - **Stage 2 (Degradation):** Response latency escalates (~380ms), Warning state.
   - **Stage 3 (Packet Loss):** Critical latency and 20% packet loss.
   - **Stage 4 (High SLA Risk):** ML probability jumps to 82%, triggering proactive early warning in Alert stream!
   - **Stage 5 (Outage):** Confirmed DOWN after 2 failures, incident opened, budget rapidly burns.
   - **Stage 6 (Recovery):** Service recovers, incident auto-resolved, MTTR recorded.
4. Watch the live dashboard update instantaneously via WebSockets!

---

## 📚 Documentation Links

- [Architecture & Layer Decoupling](file:///d:/nms_project/docs/architecture.md)
- [REST & WebSocket API Reference](file:///d:/nms_project/docs/api.md)
- [Heavy ML Pipeline & Feature Store](file:///d:/nms_project/docs/ml_pipeline.md)
- [SLA & Downtime Budget Calculation](file:///d:/nms_project/docs/sla_calculation.md)
- [Interactive Demo Guide](file:///d:/nms_project/docs/demo.md)
