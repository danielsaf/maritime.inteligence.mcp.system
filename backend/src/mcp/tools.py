import json
import logging
from src.db.repository import AISRepository
from src.core.anomalies import AnomalyDetector

# Logger configuration
logger = logging.getLogger("MCP_Tools")


def register_tools(mcp, repo: AISRepository, detector: AnomalyDetector):
    """
    Registers executable tools for the MCP (Model Context Protocol) server.

    These tools allow the AI to interact directly with the maritime database
    and the security analysis engine, enabling real-time responses to queries.
    """

    @mcp.tool()
    async def get_ships_in_area(lat: float, lon: float, radius_km: float = 50.0) -> str:
        """
        Retrieves a list of vessels within a specified radius from GPS coordinates.

        Use this tool to identify nearby traffic or assess density around
        critical infrastructure.

        Args:
            lat (float): Center latitude.
            lon (float): Center longitude.
            radius_km (float): Search radius in kilometers (default 50.0).
        """
        try:
            logger.info(f"🔍 MCP Tool Call: Fetching vessels near ({lat}, {lon}) in {radius_km}km radius.")
            vessels = await repo.get_vessels_in_radius(lat, lon, radius_km)
            return json.dumps(vessels, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Database error during vessel lookup: {e}")
            return f"Database error occurred: {str(e)}"

    @mcp.tool()
    async def analyze_maritime_security(threshold_min: int = 15) -> str:
        """
        Performs advanced security analysis: Dead Reckoning and Jamming Detection.

        Scans for inactive vessels ('dark targets') and spatial signal clusters
        that may indicate potential interference or security breaches.

        Args:
            threshold_min (int): Minutes of inactivity to trigger an alert (default 15).
        """
        try:
            logger.info(f"🛡️ MCP Tool Call: Running security analysis (threshold: {threshold_min}min).")
            data = await detector.get_enhanced_anomalies(threshold_min)

            if not data["alerts"]:
                return "✅ No maritime anomalies detected in the specified time window."

            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Security analysis failed: {e}")
            return f"Analysis error occurred: {str(e)}"

    logger.info("🛠️ MCP Tools successfully registered.")