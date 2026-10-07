import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import connect_to_mongo, close_mongo_connection, get_database
from backend.app.seed.seeder import seed_initial_data
from backend.app.monitoring.scheduler import start_scheduler, stop_scheduler
from backend.app.websocket.manager import ws_manager

# API Routers
from backend.app.auth.routes import router as auth_router
from backend.app.api.services import router as services_router
from backend.app.api.monitoring import router as monitoring_router
from backend.app.api.sla import router as sla_router
from backend.app.api.incidents import router as incidents_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.risk import router as risk_router
from backend.app.api.ml import router as ml_router
from backend.app.api.forecast import router as forecast_router
from backend.app.api.explanation import router as explanation_router
from backend.app.api.reports import router as reports_router
from backend.app.api.demo import router as demo_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sla_predict.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SLA-Predict Backend Services...")
    await connect_to_mongo()
    db = get_database()
    await seed_initial_data(db)
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down SLA-Predict Backend Services...")
    stop_scheduler()
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Network Service Monitoring and Predictive SLA Violation Detection System",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local dev frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Endpoint
@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and listen for client pings/messages
            msg = await websocket.receive_text()
            logger.debug("Received WS message from client: %s", msg)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug("WebSocket exception: %s", e)
        ws_manager.disconnect(websocket)

# Include API Routers under /api and root (for maximum proxy compatibility)
api_prefix = settings.API_V1_PREFIX
routers = [
    auth_router,
    services_router,
    monitoring_router,
    sla_router,
    incidents_router,
    alerts_router,
    risk_router,
    ml_router,
    forecast_router,
    explanation_router,
    reports_router,
    demo_router,
]

for r in routers:
    app.include_router(r, prefix=api_prefix)
    app.include_router(r)  # also accessible without /api prefix


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs": "/docs",
        "mode": "Demonstration / Production-Grade College NMS"
    }

@app.get("/health")
async def health_check():
    return {"status": "HEALTHY", "db_connected": True}
