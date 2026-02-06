import asyncio
import os
import logging
import uvicorn
import warnings
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastmcp import FastMCP

# Core and database layer imports
from src.db.session import wait_for_db
from src.db.repository import AISRepository
from src.api.ais_client import start_ais_ingestion
from src.core.anomalies import AnomalyDetector

# MCP Modules and WebSocket manager
from src.mcp.tools import register_tools
from src.mcp.prompts import register_prompts
from src.mcp.resources import register_resources
from src.api.broadcaster import manager

# 1. Suppress deprecation warnings for clean logs (Python 3.13+)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn")

# 2. Global Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MaritimeMain")

load_dotenv()

# 3. Server Initialization
mcp = FastMCP("Maritime-Intelligence-System")
app = FastAPI(
    title="Maritime Real-time API",
    description="Backend API for real-time vessel tracking and security analysis."
)

# 4. CORS Configuration
# Essential for connecting the React frontend (e.g., Vite on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. System Component Initialization
db_url = os.getenv("DB_URL")
repo = AISRepository(db_url)
detector = AnomalyDetector(repo)

# --- MCP MODULE REGISTRATION ---
register_tools(mcp, repo, detector)
register_prompts(mcp)
register_resources(mcp)


# --- HTTP ENDPOINTS (API & Documentation) ---

@app.get("/vessels")
async def get_vessels():
    """
    Returns a list of all vessels currently in the system.
    Defaults to a 500km radius around the North Sea center.
    """
    try:
        vessels = await repo.get_vessels_in_radius(60.0, 10.0, 500.0)
        return {"status": "success", "count": len(vessels), "data": vessels}
    except Exception as e:
        logger.error(f"❌ Error fetching vessels: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/force-alarm/{severity}")
async def force_alarm(severity: str):
    """
    Simulates a security breach alert for testing purposes.
    Broadcasts the alert to all connected WebSocket clients.
    """
    num_clients = len(manager.active_connections)
    sev = severity.upper()
    if sev not in ["CRITICAL", "WARNING", "INFO"]:
        sev = "CRITICAL"

    alert_msg = {
        "type": "ALERT",
        "vessel": f"SIM_TEST_{sev}",
        "data": {
            "name": "Manual Test Zone",
            "severity": sev
        }
    }

    await manager.broadcast(alert_msg)
    logger.info(f"🚨 Manual alert triggered: {sev} (Clients: {num_clients})")
    return {
        "status": "SUCCESS",
        "active_clients": num_clients,
        "sent_severity": sev
    }

# --- WEBSOCKET ENDPOINTS ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time data feed for the React dashboard.
    Manages client connection lifecycle and broadcasts live AIS updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keeps connection alive by waiting for client heartbeats
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


async def run_logic():
    """
    Core business logic loop: Manages Database connectivity and AIS data stream.
    """
    logger.info("🚢 Initializing core maritime logic...")

    await wait_for_db(db_url)
    await repo.initialize()

    api_key = os.getenv("AIS_API_KEY")
    ingestion_task = None

    if api_key:
        logger.info("📡 Launching background AIS ingestion task...")
        ingestion_task = asyncio.create_task(start_ais_ingestion(repo, api_key, detector))
    else:
        logger.warning("⚠️ AIS_API_KEY missing. System running in read-only mode.")

    try:
        # Keep the logic loop alive
        while True:
            await asyncio.sleep(3600)
    finally:
        if ingestion_task:
            ingestion_task.cancel()
        await repo.close()
        logger.info("⚓ Core logic shut down.")


async def start_all():
    """
    Orchestrator: Runs FastAPI, MCP, and AIS ingestion simultaneously.
    Supports both full-stack mode and MCP-only mode for Claude Desktop.
    """
    is_mcp_mode = os.environ.get("MCP_MODE", "false").lower() == "true"

    if is_mcp_mode:
        logger.info("🤖 Starting in MCP-ONLY mode for Claude Desktop.")
        await asyncio.gather(
            mcp.run_async(),
            run_logic()
        )
    else:
        logger.info("🚀 Starting Full Maritime Intelligence Stack (Port 8000)...")
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            ws="wsproto"
        )
        server = uvicorn.Server(config)

        await asyncio.gather(
            server.serve(),
            mcp.run_async(),
            run_logic()
        )


if __name__ == "__main__":
    try:
        asyncio.run(start_all())
    except KeyboardInterrupt:
        logger.info("⚓ Manual system shutdown initiated.")