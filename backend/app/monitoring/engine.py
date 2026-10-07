import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.monitoring.rules import evaluate_raw_check, update_anti_flapping_state
from backend.app.monitoring.http_checker import check_http
from backend.app.monitoring.ping_checker import check_ping
from backend.app.monitoring.tcp_checker import check_tcp
from backend.app.monitoring.dns_checker import check_dns
from backend.app.incidents.manager import IncidentManager
from backend.app.alerts.manager import AlertManager
from backend.app.schemas.alert import AlertType, AlertSeverity
from backend.app.schemas.service import ServiceStatus, ServiceType
from backend.app.websocket.manager import ws_manager

logger = logging.getLogger("sla_predict.monitoring")

class MonitoringEngine:
    @staticmethod
    async def run_single_check(db: AsyncIOMotorDatabase, service: dict) -> Dict[str, Any]:
        """
        Executes an asynchronous check for a single service,
        applies authoritative status evaluation & anti-flapping,
        updates database, triggers incidents/alerts, and broadcasts updates.
        """
        service_id = service["service_id"]
        service_name = service.get("name", service_id)
        service_type = service.get("type", "HTTP")
        timeout = float(service.get("timeout_seconds", 5.0))

        # 1. Execute protocol-specific check
        raw_result = {}
        try:
            if service_type in (ServiceType.HTTP.value, ServiceType.HTTPS.value):
                url = service.get("url") or f"http://{service['target']}"
                raw_result = await check_http(url=url, timeout_seconds=timeout)
            elif service_type == ServiceType.PING.value:
                raw_result = await check_ping(target=service["target"], timeout_seconds=timeout)
            elif service_type == ServiceType.TCP.value:
                port = int(service.get("port", 80))
                raw_result = await check_tcp(target=service["target"], port=port, timeout_seconds=timeout)
            elif service_type == ServiceType.DNS.value:
                raw_result = await check_dns(target=service["target"], timeout_seconds=timeout)
            else:
                raw_result = {"success": False, "response_time_ms": 0.0, "packet_loss_percent": 100.0, "error": f"Unsupported service type {service_type}"}
        except Exception as e:
            raw_result = {"success": False, "response_time_ms": 0.0, "packet_loss_percent": 100.0, "error": f"Probe exception: {str(e)[:80]}"}

        # 2. Deterministic rule evaluation
        raw_status = evaluate_raw_check(
            service_type=ServiceType(service_type),
            success=raw_result.get("success", False),
            response_time_ms=raw_result.get("response_time_ms", 0.0),
            packet_loss_percent=raw_result.get("packet_loss_percent", 0.0),
            expected_ms=float(service.get("expected_response_ms", 200.0)),
            warning_ms=float(service.get("warning_response_ms", 400.0)),
            critical_ms=float(service.get("critical_response_ms", 800.0)),
            error=raw_result.get("error")
        )

        # 3. Anti-flapping filter
        curr_state = service.get("current_state", {})
        stored_status = ServiceStatus(curr_state.get("status", ServiceStatus.UNKNOWN.value))
        consecutive_fails = int(curr_state.get("consecutive_failures", 0))
        consecutive_succs = int(curr_state.get("consecutive_successes", 0))

        new_status, new_fails, new_succs, state_changed = update_anti_flapping_state(
            current_stored_status=stored_status,
            raw_status=raw_status,
            consecutive_failures=consecutive_fails,
            consecutive_successes=consecutive_succs,
            consecutive_failures_down=int(service.get("consecutive_failures_down", 2)),
            consecutive_successes_recovery=int(service.get("consecutive_successes_recovery", 2))
        )

        now = datetime.now(timezone.utc)

        # 4. Store normalized check in MongoDB
        check_doc = {
            "service_id": service_id,
            "timestamp": now,
            "check_type": service_type,
            "success": raw_result.get("success", False),
            "status": new_status.value,
            "raw_status": raw_status.value,
            "response_time_ms": raw_result.get("response_time_ms", 0.0),
            "packet_loss_percent": raw_result.get("packet_loss_percent", 0.0),
            "error": raw_result.get("error"),
            "details": raw_result.get("details", {})
        }
        await db.checks.insert_one(check_doc)

        # 5. Update service's current state
        updated_state = {
            "status": new_status.value,
            "previous_status": stored_status.value,
            "response_time_ms": raw_result.get("response_time_ms", 0.0),
            "packet_loss_percent": raw_result.get("packet_loss_percent", 0.0),
            "consecutive_failures": new_fails,
            "consecutive_successes": new_succs,
            "last_check": now,
            "last_error": raw_result.get("error"),
            "in_flapping_state": (new_fails > 0 and new_fails < int(service.get("consecutive_failures_down", 2)))
        }
        await db.services.update_one(
            {"service_id": service_id},
            {"$set": {"current_state": updated_state, "updated_at": now}}
        )

        # 6. Incident and Alert triggers on state transitions
        if state_changed:
            if new_status == ServiceStatus.DOWN:
                err_msg = raw_result.get("error") or "Unreachable destination"
                await IncidentManager.handle_service_down(
                    db=db,
                    service_id=service_id,
                    service_name=service_name,
                    reason=err_msg
                )
                await AlertManager.trigger_alert(
                    db=db,
                    service_id=service_id,
                    service_name=service_name,
                    alert_type=AlertType.SERVICE_DOWN,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Service '{service_name}' confirmed DOWN: {err_msg}"
                )
            elif stored_status == ServiceStatus.DOWN and new_status != ServiceStatus.DOWN:
                # Service recovered
                await IncidentManager.handle_service_recovery(
                    db=db,
                    service_id=service_id,
                    service_name=service_name
                )
                await AlertManager.trigger_alert(
                    db=db,
                    service_id=service_id,
                    service_name=service_name,
                    alert_type=AlertType.SERVICE_RECOVERY,
                    severity=AlertSeverity.INFO,
                    message=f"Service '{service_name}' recovered to {new_status.value}."
                )

        # 7. WebSocket live event broadcast
        broadcast_payload = {
            "event": "service_checked",
            "service_id": service_id,
            "service_name": service_name,
            "status": new_status.value,
            "raw_status": raw_status.value,
            "response_time_ms": raw_result.get("response_time_ms", 0.0),
            "packet_loss_percent": raw_result.get("packet_loss_percent", 0.0),
            "timestamp": now.isoformat(),
            "state_changed": state_changed
        }
        await ws_manager.broadcast(broadcast_payload)

        return check_doc

    @staticmethod
    async def run_all_checks(db: AsyncIOMotorDatabase):
        """Asynchronously executes checks across all enabled services"""
        cursor = db.services.find({"enabled": True})
        services = await cursor.to_list(length=200)
        if not services:
            return

        tasks = [MonitoringEngine.run_single_check(db, s) for s in services]
        await asyncio.gather(*tasks, return_exceptions=True)
