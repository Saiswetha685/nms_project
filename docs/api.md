# SLA-Predict — REST & WebSocket API Reference

Base URL: `/api`

## Authentication
- `POST /auth/login` — Authenticate and retrieve JWT token.
- `GET /auth/me` — Retrieve current authenticated user profile.
- `POST /auth/logout` — Invalidate user session.

## Services Registry
- `GET /services` — List all registered monitored services.
- `POST /services` — Register a new network target (Admin required).
- `GET /services/{id}` — Fetch service metadata and live state.
- `PUT /services/{id}` — Update configuration (Admin required).
- `DELETE /services/{id}` — Remove service and its telemetry (Admin required).

## Monitoring & Telemetry
- `GET /services/{id}/checks` — Historical probe checks list (supports `limit`).
- `GET /services/{id}/status` — Current probe state and flapping counts.
- `POST /services/{id}/check` — Execute on-demand asynchronous probe.
- `POST /monitoring/run-all` — Trigger fleet-wide probe iteration.

## SLA & Downtime Budget
- `GET /services/{id}/sla` — Authoritative SLA % and downtime budget breakdown.
- `GET /services/{id}/sla/history` — 7-day daily availability audit.
- `GET /sla/overview` — Fleet-wide compliance summary.

## Incidents Lifecycle
- `GET /incidents` — List all tickets (optional `?status=OPEN|ACKNOWLEDGED|RESOLVED`).
- `GET /incidents/{id}` — Retrieve incident details and MTTR duration.
- `POST /incidents/{id}/acknowledge` — Acknowledge ongoing outage.
- `POST /incidents/{id}/resolve` — Confirm resolution with root cause notes.

## Alerts Stream
- `GET /alerts` — Retrieve alerts stream (optional `?unack_only=true`).
- `POST /alerts/{id}/acknowledge` — Mark alert acknowledged.

## Predictive Risk & ML Pipeline
- `GET /services/{id}/sla-risk` — Transparent rule-based 0-100 risk baseline.
- `GET /services/{id}/combined-risk` — Weighted multi-signal risk index.
- `GET /ml/services/{id}/risk` — 6-hour ML failure probability and top factors.
- `GET /ml/models` — Active model registry and evaluation metadata.
- `POST /ml/train` — Train tree ensemble pipeline (Admin required).
- `GET /ml/evaluation` — Empirical comparison: Rule Baseline vs Heavy ML.

## Statistical Forecasting & AI
- `GET /services/{id}/forecast` — Holt-Winters budget exhaustion ETA with 95% CI.
- `GET /services/{id}/explanation` — Claude LLM operational root cause brief.

## Audit Reports
- `GET /reports/executive-summary` — System overview with executive narrative.
- `GET /reports/sla` — Tabular SLA audit records.
- `GET /reports/availability` — Raw uptime and failure counts.
- `GET /reports/export/csv` — Stream CSV file (`?type=sla|availability|risk`).
- `GET /reports/export/pdf` — Stream ReportLab PDF executive audit report.

## Demo Simulation
- `POST /demo/sla-risk/stage/{stage}` — Inject Stage 1 to 6 scenario.
- `GET /demo/status` — Current simulation status.

## WebSocket
- `ws://localhost:8000/ws/live` — Real-time telemetry, check events, and simulation broadcasts.
