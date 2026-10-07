import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from backend.app.schemas.incident import IncidentStatus, IncidentSeverity

logger = logging.getLogger("sla_predict.incidents")

class IncidentManager:
    @staticmethod
    async def handle_service_down(
        db: AsyncIOMotorDatabase,
        service_id: str,
        service_name: str,
        reason: str
    ) -> Optional[dict]:
        """
        Creates an incident when a service is confirmed DOWN.
        Checks if an active incident (OPEN or ACKNOWLEDGED) already exists to avoid duplicates.
        """
        active_incident = await db.incidents.find_one({
            "service_id": service_id,
            "status": {"$in": [IncidentStatus.OPEN.value, IncidentStatus.ACKNOWLEDGED.value]}
        })
        if active_incident:
            return None  # Incident already tracking this outage

        now = datetime.now(timezone.utc)
        incident_doc = {
            "incident_id": f"inc_{uuid.uuid4().hex[:10]}",
            "service_id": service_id,
            "service_name": service_name,
            "started_at": now,
            "detected_at": now,
            "ended_at": None,
            "duration_minutes": None,
            "severity": IncidentSeverity.CRITICAL.value,
            "status": IncidentStatus.OPEN.value,
            "root_cause": reason or "Service probe consecutive failures reached threshold",
            "description": f"Service '{service_name}' transitioned to confirmed DOWN state. {reason or ''}",
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved_at": None,
            "created_at": now
        }
        await db.incidents.insert_one(incident_doc)
        logger.warning("Created new incident %s for service %s", incident_doc["incident_id"], service_id)
        return incident_doc

    @staticmethod
    async def handle_service_recovery(
        db: AsyncIOMotorDatabase,
        service_id: str,
        service_name: str
    ) -> List[dict]:
        """
        Resolves open or acknowledged incidents when a service recovers.
        Calculates downtime duration and MTTR.
        """
        now = datetime.now(timezone.utc)
        cursor = db.incidents.find({
            "service_id": service_id,
            "status": {"$in": [IncidentStatus.OPEN.value, IncidentStatus.ACKNOWLEDGED.value]}
        })
        resolved_list = []
        async for inc in cursor:
            started = inc["started_at"]
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            duration_mins = max(0.1, round((now - started).total_seconds() / 60.0, 2))
            
            await db.incidents.update_one(
                {"_id": inc["_id"]},
                {
                    "$set": {
                        "status": IncidentStatus.RESOLVED.value,
                        "ended_at": now,
                        "resolved_at": now,
                        "duration_minutes": duration_mins,
                        "resolution_notes": "Service successfully recovered and passed consecutive health checks."
                    }
                }
            )
            inc["status"] = IncidentStatus.RESOLVED.value
            inc["ended_at"] = now
            inc["duration_minutes"] = duration_mins
            resolved_list.append(inc)
            logger.info("Resolved incident %s for service %s after %.2f mins", inc["incident_id"], service_id, duration_mins)
        return resolved_list

    @staticmethod
    async def calculate_mttd_mttr(db: AsyncIOMotorDatabase) -> Dict[str, float]:
        """Calculate system-wide Mean Time to Detect and Mean Time to Resolve (in minutes)"""
        resolved_cursor = db.incidents.find({"status": IncidentStatus.RESOLVED.value})
        durations = []
        detect_lags = []
        async for inc in resolved_cursor:
            durations.append(inc.get("duration_minutes", 0.0) or 0.0)
            if inc.get("started_at") and inc.get("detected_at"):
                s = inc["started_at"]
                d = inc["detected_at"]
                detect_lags.append(max(0.0, (d - s).total_seconds() / 60.0))
        
        avg_mttr = round(sum(durations) / len(durations), 2) if durations else 0.0
        avg_mttd = round(sum(detect_lags) / len(detect_lags), 2) if detect_lags else 0.5
        return {
            "avg_mttr_minutes": avg_mttr,
            "avg_mttd_minutes": avg_mttd,
            "total_incidents": await db.incidents.count_documents({}),
            "open_incidents": await db.incidents.count_documents({"status": {"$in": [IncidentStatus.OPEN.value, IncidentStatus.ACKNOWLEDGED.value]}})
        }
