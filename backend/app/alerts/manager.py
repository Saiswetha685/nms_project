import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from backend.app.config import settings
from backend.app.schemas.alert import AlertType, AlertSeverity

logger = logging.getLogger("sla_predict.alerts")

class AlertManager:
    @staticmethod
    async def trigger_alert(
        db: AsyncIOMotorDatabase,
        service_id: str,
        service_name: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        cooldown_minutes: int = 60
    ) -> Optional[dict]:
        """
        Deduplicates alerts based on alert_type and service_id within a cooldown window.
        Saves alert to MongoDB and attempts email notification if SMTP is configured.
        """
        now = datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(minutes=cooldown_minutes)

        # Check for recent identical alert within cooldown window
        recent_alert = await db.alerts.find_one({
            "service_id": service_id,
            "type": alert_type.value,
            "created_at": {"$gte": cooldown_threshold}
        })

        if recent_alert:
            logger.debug("Alert '%s' for service %s suppressed due to cooldown window", alert_type.value, service_id)
            return None

        alert_doc = {
            "alert_id": f"alt_{uuid.uuid4().hex[:10]}",
            "service_id": service_id,
            "service_name": service_name,
            "type": alert_type.value,
            "severity": severity.value,
            "message": message,
            "created_at": now,
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None
        }

        await db.alerts.insert_one(alert_doc)
        logger.info("Generated alert %s [%s] for service %s: %s", alert_doc["alert_id"], severity.value, service_name, message)

        # Asynchronously send SMTP email if configured
        if settings.SMTP_HOST and settings.SMTP_USERNAME:
            AlertManager._send_email_notification(service_name, alert_type.value, severity.value, message)

        return alert_doc

    @staticmethod
    def _send_email_notification(service_name: str, alert_type: str, severity: str, message: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{severity}] SLA-Predict Alert: {service_name} - {alert_type}"
            msg["From"] = settings.SMTP_FROM
            msg["To"] = settings.SMTP_FROM

            text_content = f"SLA-Predict Alert Notification\n\nService: {service_name}\nSeverity: {severity}\nType: {alert_type}\nMessage: {message}\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
            msg.attach(MIMEText(text_content, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email notification sent for %s", alert_type)
        except Exception as e:
            logger.warning("Failed to send SMTP email notification: %s", e)
