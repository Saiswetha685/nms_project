import random
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from backend.app.auth.security import hash_password
from backend.app.schemas.service import ServiceType, ServiceStatus

logger = logging.getLogger("sla_predict.seeder")

SEED_SERVICES = [
    {
        "service_id": "svc_student_portal",
        "name": "Student Information Portal",
        "description": "Primary academic portal for student registration, grades, and fee payments",
        "type": ServiceType.HTTP.value,
        "target": "portal.campus.edu",
        "port": 443,
        "url": "https://httpbin.org/status/200",
        "enabled": True,
        "check_interval_seconds": 30,
        "timeout_seconds": 5,
        "expected_response_ms": 150.0,
        "warning_response_ms": 350.0,
        "critical_response_ms": 700.0,
        "sla_target_percent": 99.0,
        "sla_window_days": 30,
        "count_degraded_as_downtime": False,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    },
    {
        "service_id": "svc_college_web",
        "name": "Institutional Web Portal",
        "description": "Main public facing university website and admissions gateway",
        "type": ServiceType.HTTPS.value,
        "target": "www.college.edu",
        "port": 443,
        "url": "https://httpbin.org/get",
        "enabled": True,
        "check_interval_seconds": 30,
        "timeout_seconds": 5,
        "expected_response_ms": 120.0,
        "warning_response_ms": 280.0,
        "critical_response_ms": 600.0,
        "sla_target_percent": 99.5,
        "sla_window_days": 30,
        "count_degraded_as_downtime": False,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    },
    {
        "service_id": "svc_core_dns",
        "name": "Campus Recursive DNS Service",
        "description": "Core campus domain name resolution infrastructure",
        "type": ServiceType.DNS.value,
        "target": "google.com",
        "port": 53,
        "url": None,
        "enabled": True,
        "check_interval_seconds": 20,
        "timeout_seconds": 3,
        "expected_response_ms": 30.0,
        "warning_response_ms": 80.0,
        "critical_response_ms": 200.0,
        "sla_target_percent": 99.9,
        "sla_window_days": 30,
        "count_degraded_as_downtime": True,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    },
    {
        "service_id": "svc_smtp_mail",
        "name": "Exchange Mail Gateway",
        "description": "Campus outbound SMTP relay and email services",
        "type": ServiceType.TCP.value,
        "target": "127.0.0.1",
        "port": 27017,  # Points to running local MongoDB port for reliable TCP handshake demonstration
        "url": None,
        "enabled": True,
        "check_interval_seconds": 30,
        "timeout_seconds": 4,
        "expected_response_ms": 40.0,
        "warning_response_ms": 120.0,
        "critical_response_ms": 300.0,
        "sla_target_percent": 99.0,
        "sla_window_days": 30,
        "count_degraded_as_downtime": False,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    },
    {
        "service_id": "svc_library_sys",
        "name": "Digital Library & Catalogue",
        "description": "Online repository, search catalog, and e-book circulation server",
        "type": ServiceType.HTTP.value,
        "target": "library.campus.internal",
        "port": 80,
        "url": "https://httpbin.org/status/200",
        "enabled": True,
        "check_interval_seconds": 45,
        "timeout_seconds": 5,
        "expected_response_ms": 180.0,
        "warning_response_ms": 400.0,
        "critical_response_ms": 800.0,
        "sla_target_percent": 98.5,
        "sla_window_days": 30,
        "count_degraded_as_downtime": False,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    },
    {
        "service_id": "svc_gateway_ping",
        "name": "Core Edge Gateway Router",
        "description": "Border router ping connectivity and WAN latency monitoring",
        "type": ServiceType.PING.value,
        "target": "127.0.0.1",  # Localhost ping for dependable 0% packet loss response
        "port": None,
        "url": None,
        "enabled": True,
        "check_interval_seconds": 15,
        "timeout_seconds": 2,
        "expected_response_ms": 10.0,
        "warning_response_ms": 50.0,
        "critical_response_ms": 150.0,
        "sla_target_percent": 99.95,
        "sla_window_days": 30,
        "count_degraded_as_downtime": True,
        "consecutive_failures_down": 2,
        "consecutive_successes_recovery": 2,
        "notification_enabled": True
    }
]

async def seed_initial_data(db: AsyncIOMotorDatabase):
    """Seeds default admin/operator users, services, and realistic historical telemetry"""
    logger.info("Checking initial database seed status...")
    now = datetime.now(timezone.utc)

    # 1. Seed Users
    admin_exists = await db.users.find_one({"email": "admin@slapredict.io"})
    if not admin_exists:
        admin_doc = {
            "name": "System Administrator",
            "email": "admin@slapredict.io",
            "password_hash": hash_password("Admin@123"),
            "role": "admin",
            "created_at": now
        }
        await db.users.insert_one(admin_doc)
        logger.info("Seeded administrator account: admin@slapredict.io")

    operator_exists = await db.users.find_one({"email": "operator@slapredict.io"})
    if not operator_exists:
        op_doc = {
            "name": "NOC Operations Specialist",
            "email": "operator@slapredict.io",
            "password_hash": hash_password("Operator@123"),
            "role": "operator",
            "created_at": now
        }
        await db.users.insert_one(op_doc)
        logger.info("Seeded operator account: operator@slapredict.io")

    # 2. Seed Services
    for svc_spec in SEED_SERVICES:
        existing = await db.services.find_one({"service_id": svc_spec["service_id"]})
        if not existing:
            doc = svc_spec.copy()
            doc["current_state"] = {
                "status": ServiceStatus.HEALTHY.value,
                "previous_status": ServiceStatus.HEALTHY.value,
                "response_time_ms": doc["expected_response_ms"] * 0.8,
                "packet_loss_percent": 0.0,
                "consecutive_failures": 0,
                "consecutive_successes": 15,
                "last_check": now,
                "last_error": None,
                "in_flapping_state": False
            }
            doc["created_at"] = now - timedelta(days=25)
            doc["updated_at"] = now
            await db.services.insert_one(doc)
            logger.info("Seeded service: %s (%s)", doc["name"], doc["service_id"])

    # 3. Seed Realistic Historical Checks if empty
    check_count = await db.checks.count_documents({})
    if check_count < 100:
        logger.info("Seeding realistic historical check telemetry for charts and SLA calculations...")
        all_checks = []
        random.seed(42)

        for svc in SEED_SERVICES:
            sid = svc["service_id"]
            exp = svc["expected_response_ms"]
            # Generate 120 historical checks spanning last 3 days
            for i in range(120):
                t = now - timedelta(minutes=(120 - i) * 20)
                # Occasional slight jitter or degradation for student portal
                if sid == "svc_student_portal" and 85 <= i <= 95:
                    lat = random.uniform(exp * 1.8, exp * 2.8)
                    st = ServiceStatus.WARNING.value
                    loss = random.uniform(1.0, 4.0)
                    succ = True
                elif sid == "svc_student_portal" and 96 <= i <= 97:
                    lat = random.uniform(exp * 3.5, exp * 4.5)
                    st = ServiceStatus.CRITICAL.value
                    loss = random.uniform(5.0, 15.0)
                    succ = True
                else:
                    lat = max(5.0, random.gauss(exp * 0.85, exp * 0.15))
                    st = ServiceStatus.HEALTHY.value
                    loss = 0.0
                    succ = True

                all_checks.append({
                    "service_id": sid,
                    "timestamp": t,
                    "check_type": svc["type"],
                    "success": succ,
                    "status": st,
                    "response_time_ms": round(lat, 2),
                    "packet_loss_percent": round(loss, 2),
                    "error": None,
                    "details": {"seed": True}
                })

        if all_checks:
            await db.checks.insert_many(all_checks)
            logger.info("Seeded %d historical telemetry checks successfully.", len(all_checks))
