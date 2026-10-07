from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
from backend.app.database import get_database
from backend.app.monitoring.engine import MonitoringEngine

logger = logging.getLogger("sla_predict.scheduler")

scheduler = AsyncIOScheduler()

async def scheduled_monitoring_tick():
    """Periodic tick executing all enabled service checks"""
    db = get_database()
    if db is not None:
        try:
            await MonitoringEngine.run_all_checks(db)
        except Exception as e:
            logger.error("Error during scheduled monitoring tick: %s", e)

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            scheduled_monitoring_tick,
            "interval",
            seconds=20,
            id="periodic_service_checks",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler background monitoring started (interval: 20s).")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
