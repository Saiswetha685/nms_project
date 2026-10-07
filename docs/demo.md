# SLA-Predict — Demonstration & Simulation Guide

## Overview

The interactive simulation engine provides an end-to-end demonstration of how the system handles network degradation, proactively warns operators before contractual breaches, creates tickets on outage, and validates health recovery.

## The 6 Demonstration Stages

### Stage 1: NORMAL BASELINE
- **Telemetry:** Latency ~45ms, 0% packet loss.
- **SLA:** Fully COMPLIANT, low risk score (<20).
- **Outcome:** Clean green indicators across cards and tables.

### Stage 2: LATENCY DEGRADATION
- **Telemetry:** Latency escalates to ~380ms.
- **SLA:** Status transitions to `WARNING`.
- **Outcome:** Latency risk component elevates; chart traces yellow threshold.

### Stage 3: PACKET LOSS & JITTER
- **Telemetry:** Packet loss spikes to 15–25%, latency rises to 850ms.
- **SLA:** Status transitions to `CRITICAL`.
- **Outcome:** Burn rate surges; rule risk score reaches elevated range (>50).

### Stage 4: HIGH SLA RISK (ML PROACTIVE WARNING)
- **Telemetry:** Continued jitter with high variance.
- **Intelligence:** Tree ensemble model calculates 82% failure probability in next 6h.
- **Outcome:** Proactive alert generated in the Alert Stream BEFORE an outage occurs. Claude AI copilot explains root cause.

### Stage 5: OUTAGE & SLA VIOLATION
- **Telemetry:** 100% packet loss / connection timeout.
- **Anti-Flapping:** Confirms DOWN after 2 consecutive failures.
- **Outcome:** NOC Incident opened immediately; critical alerts dispatched; downtime budget burns rapidly; status flags VIOLATED.

### Stage 6: RESTITUTION & RECOVERY
- **Telemetry:** Latency returns to ~45ms, 0% packet loss.
- **Anti-Flapping:** Confirms RECOVERY after 2 consecutive successful checks.
- **Outcome:** Incident automatically marked `RESOLVED`; MTTR recorded; recovery alert sent.
