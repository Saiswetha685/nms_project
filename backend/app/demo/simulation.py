import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.schemas.service import ServiceStatus, ServiceType
from backend.app.incidents.manager import IncidentManager
from backend.app.alerts.manager import AlertManager
from backend.app.schemas.alert import AlertType, AlertSeverity
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("sla_predict.simulation")

class SimulationEngine:
    CURRENT_STAGE: int = 1

    @classmethod
    async def trigger_stage(
        cls,
        db: AsyncIOMotorDatabase,
        stage: int,
        target_service_id: str = "svc_student_portal"
    ) -> Dict[str, Any]:
        """
        Executes controlled demonstration stage across 6 progressive scenarios:
        1: NORMAL
        2: LATENCY DEGRADATION
        3: PACKET LOSS / FAILURES
        4: HIGH SLA RISK (Proactive ML Early Warning)
        5: DOWN / SLA VIOLATION
        6: RECOVERY
        """
        cls.CURRENT_STAGE = stage
        now = datetime.now(timezone.utc)

        service = await db.services.find_one({"service_id": target_service_id})
        if not service:
            service = await db.services.find_one({})
            if not service:
                return {"error": "No services available to simulate"}
            target_service_id = service["service_id"]

        svc_name = service.get("name", "Monitored Service")
        stage_names = {
            1: "NORMAL (Healthy baseline)",
            2: "LATENCY DEGRADATION (Response time escalation)",
            3: "PACKET LOSS / FAILURES (Critical telemetry jitter)",
            4: "HIGH SLA RISK (Predictive ML Alert & Budget Pressure)",
            5: "DOWN / SLA VIOLATION (Confirmed Outage & Incident Creation)",
            6: "RECOVERY (Healthy restitution & MTTR resolution)"
        }

        # Simulation behavior based on stage
        if stage == 1:
            lat = round(random.uniform(35.0, 65.0), 1)
            loss = 0.0
            status = ServiceStatus.HEALTHY.value
            success = True
            err = None
            msg = "System operating optimally under normal load."
        elif stage == 2:
            lat = round(random.uniform(320.0, 480.0), 1)
            loss = 0.0
            status = ServiceStatus.WARNING.value
            success = True
            err = "Response latency exceeds expected baseline"
            msg = "Warning: Latency degradation observed."
        elif stage == 3:
            lat = round(random.uniform(550.0, 950.0), 1)
            loss = round(random.uniform(12.0, 25.0), 1)
            status = ServiceStatus.CRITICAL.value
            success = True
            err = "High packet loss and latency threshold breach"
            msg = "Critical: Packet loss and latency spikes detected."
        elif stage == 4:
            lat = round(random.uniform(850.0, 1400.0), 1)
            loss = round(random.uniform(35.0, 60.0), 1)
            status = ServiceStatus.CRITICAL.value
            success = True
            err = "Severe latency escalation & packet loss precursor"
            msg = "Proactive Warning: High SLA violation risk and imminent failure probability detected!"
            # Fire predictive alert
            await AlertManager.trigger_alert(
                db=db,
                service_id=target_service_id,
                service_name=svc_name,
                alert_type=AlertType.HIGH_SLA_RISK,
                severity=AlertSeverity.WARNING,
                message=f"Predictive Early Warning: '{svc_name}' has 82% probability of outage within 6h. Act proactively!",
                cooldown_minutes=1
            )
        elif stage == 5:
            lat = 0.0
            loss = 100.0
            status = ServiceStatus.DOWN.value
            success = False
            err = "Connection timed out / destination host unreachable"
            msg = "Confirmed DOWN: Service unavailable. SLA budget rapidly burning."
            # Trigger Incident
            await IncidentManager.handle_service_down(
                db=db,
                service_id=target_service_id,
                service_name=svc_name,
                reason=err
            )
            # Trigger Critical Alert
            await AlertManager.trigger_alert(
                db=db,
                service_id=target_service_id,
                service_name=svc_name,
                alert_type=AlertType.SERVICE_DOWN,
                severity=AlertSeverity.CRITICAL,
                message=f"OUTAGE: '{svc_name}' is confirmed DOWN. Immediate intervention required.",
                cooldown_minutes=1
            )
        elif stage == 6:
            lat = round(random.uniform(40.0, 75.0), 1)
            loss = 0.0
            status = ServiceStatus.HEALTHY.value
            success = True
            err = None
            msg = "Recovery: Health checks passing. Incident resolved."
            # Resolve incident
            await IncidentManager.handle_service_recovery(
                db=db,
                service_id=target_service_id,
                service_name=svc_name
            )
            # Recovery alert
            await AlertManager.trigger_alert(
                db=db,
                service_id=target_service_id,
                service_name=svc_name,
                alert_type=AlertType.SERVICE_RECOVERY,
                severity=AlertSeverity.INFO,
                message=f"RECOVERED: '{svc_name}' is healthy and accepting traffic.",
                cooldown_minutes=1
            )
        else:
            return {"error": f"Invalid stage {stage}. Must be between 1 and 6."}

        # Store check record
        check_doc = {
            "service_id": target_service_id,
            "timestamp": now,
            "check_type": service.get("type", "HTTP"),
            "success": success,
            "status": status,
            "response_time_ms": lat,
            "packet_loss_percent": loss,
            "error": err,
            "is_simulation": True,
            "details": {"simulation_stage": stage, "stage_title": stage_names.get(stage)}
        }
        await db.checks.insert_one(check_doc)

        # Update service current state
        await db.services.update_one(
            {"service_id": target_service_id},
            {
                "$set": {
                    "current_state.status": status,
                    "current_state.response_time_ms": lat,
                    "current_state.packet_loss_percent": loss,
                    "current_state.last_check": now,
                    "current_state.last_error": err,
                    "updated_at": now
                }
            }
        )

        # Broadcast simulation event on WebSocket
        await ws_manager.broadcast({
            "event": "simulation_stage_changed",
            "stage": stage,
            "stage_name": stage_names.get(stage),
            "service_id": target_service_id,
            "service_name": svc_name,
            "status": status,
            "response_time_ms": lat,
            "packet_loss_percent": loss,
            "message": msg,
            "timestamp": now.isoformat()
        })

        return {
            "stage": stage,
            "stage_name": stage_names.get(stage),
            "service_id": target_service_id,
            "service_name": svc_name,
            "status": status,
            "response_time_ms": lat,
            "packet_loss_percent": loss,
            "narrative": msg,
            "timestamp": now.isoformat()
        }
