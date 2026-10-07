from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
from backend.app.config import settings

logger = logging.getLogger("sla_predict.database")

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None
    sync_client: MongoClient = None

db_instance = Database()

def get_database() -> AsyncIOMotorDatabase:
    return db_instance.db

def get_sync_database():
    if db_instance.sync_client is None:
        db_instance.sync_client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
    return db_instance.sync_client[settings.DATABASE_NAME]

async def connect_to_mongo():
    logger.info("Connecting to MongoDB at %s...", settings.MONGODB_URI)
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        # Quick ping to verify
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB database '%s'.", settings.DATABASE_NAME)
        await create_indexes()
    except Exception as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        raise

async def close_mongo_connection():
    if db_instance.client:
        logger.info("Closing MongoDB connection...")
        db_instance.client.close()
        logger.info("MongoDB connection closed.")
    if db_instance.sync_client:
        db_instance.sync_client.close()

async def create_indexes():
    """Ensure indexes for rapid lookups and time-series aggregation"""
    db = db_instance.db
    try:
        # Users index
        await db.users.create_index([("email", ASCENDING)], unique=True)
        # Services index
        await db.services.create_index([("service_id", ASCENDING)], unique=True)
        # Checks indexes (heavily queried by service and time)
        await db.checks.create_index([("service_id", ASCENDING), ("timestamp", DESCENDING)])
        await db.checks.create_index([("timestamp", DESCENDING)])
        # Incidents
        await db.incidents.create_index([("service_id", ASCENDING), ("status", ASCENDING)])
        await db.incidents.create_index([("started_at", DESCENDING)])
        # Alerts
        await db.alerts.create_index([("service_id", ASCENDING), ("created_at", DESCENDING)])
        await db.alerts.create_index([("acknowledged", ASCENDING)])
        # SLA Risk Snapshots
        await db.sla_risk_snapshots.create_index([("service_id", ASCENDING), ("timestamp", DESCENDING)])
        # ML Models
        await db.ml_models.create_index([("version", ASCENDING)], unique=True)
        # Risk Predictions
        await db.risk_predictions.create_index([("service_id", ASCENDING), ("timestamp", DESCENDING)])
        # Audit logs
        await db.audit_logs.create_index([("timestamp", DESCENDING)])
        logger.info("MongoDB indexes verified and ensured.")
    except Exception as e:
        logger.warning("Error creating MongoDB indexes: %s", e)
