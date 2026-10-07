import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.schemas.report import (
    SLAReportItem, AvailabilityReportItem, ResponseTimeReportItem,
    IncidentReportSummary, PredictiveRiskReportItem, ExecutiveSummary
)
from backend.app.sla.calculator import SLACalculator
from backend.app.incidents.manager import IncidentManager
from backend.app.risk.rule_engine import RuleRiskEngine
from backend.app.ml.predict import MLPredictor
from backend.app.schemas.incident import IncidentResponse

logger = logging.getLogger("sla_predict.reports")

class ReportGenerator:
    @staticmethod
    async def generate_sla_report(db: AsyncIOMotorDatabase) -> List[SLAReportItem]:
        cursor = db.services.find({})
        items = []
        async for svc in cursor:
            sla_res = await SLACalculator.calculate_service_sla(db, svc)
            items.append(SLAReportItem(
                service_id=svc["service_id"],
                service_name=svc.get("name", svc["service_id"]),
                target_sla=sla_res.sla_target_percent,
                actual_sla=sla_res.availability_percent,
                downtime_minutes=sla_res.budget.used_downtime_minutes,
                remaining_budget_minutes=sla_res.budget.remaining_downtime_minutes,
                compliance_state=sla_res.compliance_state.value
            ))
        return items

    @staticmethod
    async def generate_availability_report(db: AsyncIOMotorDatabase) -> List[AvailabilityReportItem]:
        cursor = db.services.find({})
        items = []
        async for svc in cursor:
            sid = svc["service_id"]
            total = await db.checks.count_documents({"service_id": sid})
            failed = await db.checks.count_documents({"service_id": sid, "$or": [{"success": False}, {"status": "DOWN"}]})
            succ = total - failed
            uptime = round((succ / total * 100.0), 2) if total > 0 else 100.0
            interval = int(svc.get("check_interval_seconds", 30))
            downtime_mins = round((failed * interval) / 60.0, 2)

            items.append(AvailabilityReportItem(
                service_id=sid,
                service_name=svc.get("name", sid),
                type=svc.get("type", "HTTP"),
                total_checks=total,
                successful_checks=succ,
                failed_checks=failed,
                uptime_percent=uptime,
                total_downtime_minutes=downtime_mins
            ))
        return items

    @staticmethod
    async def generate_response_time_report(db: AsyncIOMotorDatabase) -> List[ResponseTimeReportItem]:
        cursor = db.services.find({})
        items = []
        async for svc in cursor:
            sid = svc["service_id"]
            checks_cursor = db.checks.find({"service_id": sid, "response_time_ms": {"$gt": 0}}).sort("timestamp", -1).limit(200)
            lats = []
            async for c in checks_cursor:
                lats.append(float(c["response_time_ms"]))

            exp = float(svc.get("expected_response_ms", 200.0))
            warn = float(svc.get("warning_response_ms", 400.0))

            if lats:
                min_lat = round(float(np.min(lats)), 1)
                avg_lat = round(float(np.mean(lats)), 1)
                max_lat = round(float(np.max(lats)), 1)
                p95_lat = round(float(np.percentile(lats, 95)), 1)
            else:
                min_lat = avg_lat = max_lat = p95_lat = 0.0

            status_str = "HEALTHY" if avg_lat <= exp else "WARNING" if avg_lat <= warn else "CRITICAL"
            items.append(ResponseTimeReportItem(
                service_id=sid,
                service_name=svc.get("name", sid),
                min_ms=min_lat,
                avg_ms=avg_lat,
                max_ms=max_lat,
                p95_ms=p95_lat,
                threshold_ms=exp,
                degradation_status=status_str
            ))
        return items

    @staticmethod
    async def generate_incident_report(db: AsyncIOMotorDatabase) -> IncidentReportSummary:
        metrics = await IncidentManager.calculate_mttd_mttr(db)
        cursor = db.incidents.find({}).sort("started_at", -1).limit(50)
        inc_list = []
        async for inc in cursor:
            inc_list.append(IncidentResponse(
                incident_id=inc["incident_id"],
                service_id=inc["service_id"],
                service_name=inc.get("service_name"),
                started_at=inc["started_at"],
                detected_at=inc["detected_at"],
                ended_at=inc.get("ended_at"),
                duration_minutes=inc.get("duration_minutes"),
                severity=inc.get("severity", "CRITICAL"),
                status=inc.get("status", "OPEN"),
                root_cause=inc.get("root_cause"),
                description=inc.get("description", ""),
                acknowledged_by=inc.get("acknowledged_by"),
                acknowledged_at=inc.get("acknowledged_at"),
                resolved_at=inc.get("resolved_at")
            ))

        return IncidentReportSummary(
            total_incidents=metrics["total_incidents"],
            open_incidents=metrics["open_incidents"],
            resolved_incidents=metrics["total_incidents"] - metrics["open_incidents"],
            avg_mttd_minutes=metrics["avg_mttd_minutes"],
            avg_mttr_minutes=metrics["avg_mttr_minutes"],
            incidents=inc_list
        )

    @staticmethod
    async def generate_predictive_risk_report(db: AsyncIOMotorDatabase) -> List[PredictiveRiskReportItem]:
        cursor = db.services.find({})
        items = []
        async for svc in cursor:
            rule_res = await RuleRiskEngine.compute_rule_risk(db, svc)
            ml_prob = None
            top_desc = "Stable baseline"
            try:
                ml_res = await MLPredictor.predict_service_risk(db, svc)
                ml_prob = ml_res.probability_down_next_6h
                if ml_res.top_features:
                    top_desc = ml_res.top_features[0].description or ml_res.top_features[0].feature
            except Exception:
                pass

            score = rule_res.rule_risk
            items.append(PredictiveRiskReportItem(
                service_id=svc["service_id"],
                service_name=svc.get("name", svc["service_id"]),
                rule_risk=score,
                ml_probability=ml_prob,
                forecast_hours=None,
                combined_risk=round(score * 0.5 + ((ml_prob or 0.1) * 50.0), 1),
                risk_level=rule_res.risk_level.value,
                top_factor=top_desc
            ))
        return items

    @staticmethod
    async def generate_executive_summary(db: AsyncIOMotorDatabase) -> ExecutiveSummary:
        now = datetime.now(timezone.utc)
        services = await db.services.find({}).to_list(length=200)
        total = len(services)
        healthy = sum(1 for s in services if s.get("current_state", {}).get("status") == "HEALTHY")
        warning = sum(1 for s in services if s.get("current_state", {}).get("status") == "WARNING")
        crit = sum(1 for s in services if s.get("current_state", {}).get("status") == "CRITICAL")
        down = sum(1 for s in services if s.get("current_state", {}).get("status") == "DOWN")

        active_inc = await db.incidents.count_documents({"status": {"$in": ["OPEN", "ACKNOWLEDGED"]}})

        # Check violations
        violations = 0
        high_risk = 0
        avails = []
        attention = []

        for s in services:
            sla_r = await SLACalculator.calculate_service_sla(db, s)
            avails.append(sla_r.availability_percent)
            if sla_r.compliance_state.value == "VIOLATED":
                violations += 1
                attention.append(f"{s['name']}: SLA Contract Violated ({sla_r.availability_percent:.2f}% < {sla_r.sla_target_percent}%)")
            elif sla_r.compliance_state.value == "AT_RISK":
                high_risk += 1
                attention.append(f"{s['name']}: SLA Downtime Budget Consumed ({sla_r.budget.budget_consumption_percent:.1f}%)")

        avg_avail = round(sum(avails) / len(avails), 2) if avails else 100.0
        if not attention:
            attention.append("All network targets are operating within nominal latency and availability budgets.")

        narrative = (
            f"Network infrastructure health is currently evaluating across {total} monitored mission-critical services. "
            f"Aggregate availability across all observation windows stands at {avg_avail:.2f}%. "
            f"There are currently {active_inc} active incidents and {violations} confirmed SLA contract violations. "
            f"Predictive ML telemetry models flag {high_risk} services warranting preemptive engineering intervention."
        )

        return ExecutiveSummary(
            generated_at=now,
            total_services=total,
            healthy_services=healthy,
            warning_services=warning,
            critical_services=crit,
            down_services=down,
            sla_violations_count=violations,
            high_risk_services_count=high_risk,
            active_incidents_count=active_inc,
            average_availability_percent=avg_avail,
            executive_narrative=narrative,
            attention_areas=attention
        )
