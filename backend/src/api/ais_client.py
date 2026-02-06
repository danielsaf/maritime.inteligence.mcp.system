import asyncio
import json
import websockets
import ssl
import certifi
import logging
from src.api.broadcaster import manager
from src.db.repository import AISRepository
from src.core.anomalies import AnomalyDetector

# Logger configuration
logger = logging.getLogger(__name__)


async def start_ais_ingestion(repo: AISRepository, api_key: str, detector: AnomalyDetector):
    """
    Asynchronous client for receiving AIS data from AISStream.

    Processes incoming vessel data for security violations (Geofencing)
    before persisting to the database and broadcasting to connected clients.

    Args:
        repo (AISRepository): Repository for database operations.
        api_key (str): AISStream API authentication key.
        detector (AnomalyDetector): Security engine for geofence analysis.
    """
    # Buffer queue to handle high-volume data streams
    queue = asyncio.Queue(maxsize=5000)

    async def db_writer():
        """
        Consumer task that processes buffered data in batches.

        Handles periodic flushing to the database and real-time alerts
        triggering when geofence violations are detected.
        """
        logger.info("👷 Database consumer and alert engine started.")
        batch_size = 50
        buffer = []
        total_processed = 0

        while True:
            try:
                try:
                    # Wait for data with a 5s timeout to ensure periodic flushing
                    data = await asyncio.wait_for(queue.get(), timeout=5.0)
                    buffer.append(data)
                except asyncio.TimeoutError:
                    if buffer:
                        await process_and_flush(buffer)
                        total_processed += len(buffer)
                        buffer.clear()
                    continue

                if len(buffer) >= batch_size:
                    await process_and_flush(buffer)
                    total_processed += len(buffer)
                    logger.info(
                        f"📊 Batch Flush: {len(buffer)} records. Queue size: {queue.qsize()} | Total: {total_processed}"
                    )
                    buffer.clear()

                queue.task_done()

            except Exception as e:
                logger.error(f"❌ Consumer error: {e}")
                await asyncio.sleep(1)

    async def process_and_flush(vessel_batch):
        """
        Orchestrates analysis, broadcasting, and database storage for a batch of vessels.

        Args:
            vessel_batch (list): List of normalized vessel data dictionaries.
        """
        # A. REAL-TIME ANALYSIS (Geofencing)
        for v in vessel_batch:
            violation = await detector.check_geofence_violation(v['lat'], v['lon'])
            if violation:
                logger.warning(f"🚨 GEOFENCE ALERT: {v['name']} in {violation['name']}")
                # Broadcast alert to the frontend
                await manager.broadcast({
                    "type": "ALERT",
                    "data": violation,
                    "vessel": v['name']
                })

        # B. LIVE MAP BROADCAST
        # Update frontend with new vessel positions
        await manager.broadcast({"type": "VESSEL_UPDATE", "data": vessel_batch})

        # C. DATABASE PERSISTENCE
        await repo.update_vessels_batch(vessel_batch)

    # Launch consumer task in the background
    asyncio.create_task(db_writer())

    # 2. PRODUCER - Receives raw data from AISStream WebSocket
    url = "wss://stream.aisstream.io/v0/stream"
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    subscribe_msg = {
        "APIKey": api_key,
        "BoundingBoxes": [[[57.0, 3.0], [65.0, 15.0]]]  # Norwegian EEZ and North Sea
    }

    while True:
        try:
            async with websockets.connect(
                    url,
                    ssl=ssl_context,
                    ping_interval=20,
                    ping_timeout=20
            ) as ws:
                await ws.send(json.dumps(subscribe_msg))
                logger.info("📡 AISStream subscription active.")

                async for message in ws:
                    msg = json.loads(message)
                    meta = msg.get("MetaData", {})

                    # Data normalization logic
                    vessel_data = {
                        "mmsi": meta.get("MMSI"),
                        "name": meta.get("ShipName", "Unknown").strip(),
                        "lat": meta.get("latitude"),
                        "lon": meta.get("longitude"),
                        "speed": (msg.get("Message", {}).get("PositionReport") or
                                  msg.get("Message", {}).get("StandardClassBPositionReport") or {}).get("Sog", 0),
                        "course": (msg.get("Message", {}).get("PositionReport") or
                                   msg.get("Message", {}).get("StandardClassBPositionReport") or {}).get("Cog", 0),
                        "vessel_type": msg.get("MessageType", "Unknown")
                    }

                    if vessel_data["mmsi"] and vessel_data["lat"] is not None:
                        try:
                            queue.put_nowait(vessel_data)
                        except asyncio.QueueFull:
                            logger.warning("⚠️ Processing queue full! Data loss may occur.")

        except Exception as e:
            logger.error(f"⚠️ AISStream connection lost: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)