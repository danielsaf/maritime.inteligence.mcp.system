import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

# Logger configuration
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Core security engine for maritime anomaly detection.

    Responsible for calculating Dead Reckoning positions, verifying geofence
    violations, and identifying potential security threats like signal jamming clusters.
    """

    def __init__(self, repo):
        """
        Initializes the detector with a data repository.

        Args:
            repo: The maritime repository for database spatial queries.
        """
        self.repo = repo

    def calculate_predicted_pos(self, lat: float, lon: float, speed: float, course: float, last_seen: datetime) -> Dict[
        str, float]:
        """
        Calculates the predicted position of a vessel using Dead Reckoning logic.

        Uses spherical trigonometry to estimate current location based on the
        last known speed, course, and elapsed time.

        Args:
            lat (float): Last known latitude.
            lon (float): Last known longitude.
            speed (float): Vessel speed in knots (SOG).
            course (float): Vessel course in degrees (COG).
            last_seen (datetime): Timestamp of the last received AIS message.

        Returns:
            Dict[str, float]: A dictionary containing predicted 'lat' and 'lon'.
        """
        if speed < 0.5:
            return {"lat": lat, "lon": lon}

        # Time difference in hours
        hours_passed = (datetime.now(timezone.utc) - last_seen).total_seconds() / 3600.0
        dist_nm = speed * hours_passed

        # Simplified spherical trigonometry (Rhumb Line approximation)
        # 1 minute of latitude = 1 nautical mile
        d_lat = (dist_nm * math.cos(math.radians(course))) / 60.0
        d_lon = (dist_nm * math.sin(math.radians(course))) / (60.0 * math.cos(math.radians(lat)))

        return {
            "lat": round(lat + d_lat, 6),
            "lon": round(lon + d_lon, 6)
        }

    async def check_geofence_violation(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Verifies if a specific coordinate violates any active geofence zones.

        Args:
            lat (float): Current latitude.
            lon (float): Current longitude.

        Returns:
            Optional[Dict]: Data of the breached zone if violation exists, else None.
        """
        try:
            return await self.repo.check_point_in_geofence(lat, lon)
        except Exception as e:
            logger.error(f"❌ Geofence verification failed: {e}")
            return None

    async def get_enhanced_anomalies(self, threshold_min: int = 15) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregates maritime anomalies for the MCP (Model Context Protocol) server.

        Identifies vessels that have stopped transmitting (Dark Targets) and
        detects spatial clusters of lost signals which may indicate GPS jamming.

        Args:
            threshold_min (int): Inactivity threshold in minutes. Default is 15.

        Returns:
            Dict: Lists of 'alerts' (vessels) and 'clusters' (potential jamming zones).
        """
        vessels = await self.repo.get_inactive_vessels(threshold_min)
        if not vessels:
            logger.info("✅ No maritime anomalies detected in the current window.")
            return {"alerts": [], "clusters": []}

        alerts = []
        for v in vessels:
            predicted = self.calculate_predicted_pos(
                v['lat'], v['lon'], v['speed'], v.get('course', 0), v['last_seen']
            )
            alerts.append({
                "mmsi": v['mmsi'],
                "name": v['name'],
                "speed": v['speed'],
                "last_seen": v['last_seen'],
                "last_pos": {"lat": v['lat'], "lon": v['lon']},
                "predicted_pos": predicted
            })

        # Cluster detection for signal loss (potential jamming)
        clusters = []
        for i, a1 in enumerate(alerts):
            nearby = []
            for j, a2 in enumerate(alerts):
                if i == j: continue
                # Simple Euclidean distance for clustering (approx. 0.1 deg ~= 10km)
                dist = math.sqrt((a1['last_pos']['lat'] - a2['last_pos']['lat']) ** 2 +
                                 (a1['last_pos']['lon'] - a2['last_pos']['lon']) ** 2)
                if dist < 0.1:
                    nearby.append(a2['mmsi'])

            if len(nearby) >= 2:
                clusters.append({
                    "center": a1['last_pos'],
                    "affected_mmsi": [a1['mmsi']] + nearby,
                    "type": "POTENTIAL_JAMMING_ZONE"
                })

        logger.warning(f"🚨 Found {len(alerts)} inactive vessels and {len(clusters)} jamming clusters.")
        return {"alerts": alerts, "clusters": clusters}