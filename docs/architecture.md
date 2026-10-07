# SLA-Predict — Architecture Specification

## 1. System Overview

SLA-Predict is a dual-tier hybrid Network Management System (NMS) designed to monitor mission-critical services, calculate auditable deterministic availability metrics, and project short-term SLA risk using Machine Learning and statistical forecasting.

```
                           Network Targets
                     (HTTP, HTTPS, Ping, TCP, DNS)
                                  │
                                  ▼
                       Async Monitoring Engine
                      (httpx, icmplib, dnspython)
                                  │
                                  ▼
                   Authoritative Deterministic Layer
               ┌──────────────────┴──────────────────┐
               │                                     │
               ▼                                     ▼
        Status Evaluator                      SLA Calculator
   (Healthy / Warn / Crit / Down)        (Availability %, Budget)
               │                                     │
               ▼                                     ▼
      Anti-Flapping Filter                  Downtime Budget Burn
               │                                     │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
                   Rule-Based SLA Risk Baseline (0-100)
                                  │
                   Predictive Intelligence Layer
               ┌──────────────────┴──────────────────┐
               │                                     │
               ▼                                     ▼
       Heavy ML Pipeline                   Statistical Forecast
    (XGBoost / GradBoost)                     (Holt-Winters)
  6h Failure Probability                  Budget Exhaustion ETA
               │                                     │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
                        Combined Risk Engine
                                  │
                                  ▼
                        LLM Copilot (Claude)
                     Operational Risk Synthesis
                                  │
                                  ▼
                       Proactive Notification
                     (WebSockets, SMTP, Alerts)
```

## 2. Decoupled Core Principles

1. **Deterministic Decision Layer (Authoritative Ground Truth):**
   - Service state (HEALTHY, WARNING, CRITICAL, DOWN)
   - Contractual Availability %
   - Downtime Budget Consumption
   - Incidents Creation & Resolution
   - Anti-flapping hysteresis

2. **Predictive Intelligence Layer (Advisory Early Warning):**
   - Tree ensemble failure probability (within next 6 hours)
   - Feature attribution and telemetry velocity
   - Holt-Winters budget exhaustion ETA
   - Proactive NOC early alerts
   - Natural language explanations via Claude

Under NO circumstances does the predictive layer modify authoritative status or SLA compliance.
