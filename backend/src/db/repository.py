import logging
import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from typing import List, Dict, Any, Optional

# Logger configuration
logger = logging.getLogger(__name__)


class AISRepository:
    """
    Data Access Object (DAO) for maritime data stored in PostGIS.

    Handles high-frequency vessel updates, spatial geofence lookups,
    and anomaly detection queries using asynchronous connection pooling.
    """

    def __init__(self, db_url: str):
        """
        Initializes the repository with a PostgreSQL connection string.

        Args:
            db_url (str): Connection string (e.g., postgresql://user:pass@host:port/db)
        """
        self.db_url = db_url
        self.pool = AsyncConnectionPool(
            conninfo=db_url,
            min_size=2,
            max_size=10,
            open=False
        )

    async def initialize(self):
        """
        Opens the asynchronous connection pool and waits for readiness.
        """
        await self.pool.open()
        await self.pool.wait()
        logger.info("📡 Database connection pool initialized and ready.")

    async def close(self):
        """
        Gracefully closes all active database connections in the pool.
        """
        await self.pool.close()
        logger.info("🔌 Database connection pool closed.")

    async def update_vessels_batch(self, vessels_list: List[Dict[str, Any]]):
        """
        Performs a batch upsert of vessel positions and metadata.

        Optimizes database performance by using 'executemany' and handles
        coordinate transformation to geography types.

        Args:
            vessels_list (List[Dict]): List of normalized vessel data.
        """
        if not vessels_list:
            return

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                data_tuples = [
                    (v['mmsi'], v['name'], v['lon'], v['lat'], v['speed'], v['course'], v['vessel_type'])
                    for v in vessels_list
                ]
                await cur.executemany("""
                                      INSERT INTO vessels (mmsi, name, last_pos, speed, course, type, last_seen)
                                      VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s, %s, %s,
                                              NOW()) ON CONFLICT (mmsi) DO
                                      UPDATE SET
                                          last_pos = EXCLUDED.last_pos,
                                          speed = EXCLUDED.speed,
                                          course = EXCLUDED.course,
                                          last_seen = NOW();
                                      """, data_tuples)

    async def check_point_in_geofence(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Performs a spatial point-in-polygon check against all active geofences.

        Args:
            lat (float): Vessel latitude.
            lon (float): Vessel longitude.

        Returns:
            Optional[Dict]: Zone name and severity if inside a geofence, else None.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # ST_Contains evaluates if the point is within the geofence polygon
                await cur.execute("""
                                  SELECT name, severity
                                  FROM geofences
                                  WHERE ST_Contains(area::geometry, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geometry) LIMIT 1;
                                  """, (lon, lat))
                return await cur.fetchone()

    async def get_inactive_vessels(self, minutes: int) -> List[Dict[str, Any]]:
        """
        Identifies vessels that haven't transmitted a signal within the specified window.

        Useful for detecting potential sensor failure or intentional signal blackout.

        Args:
            minutes (int): Inactivity threshold in minutes.

        Returns:
            List[Dict]: Inactive vessel records with their last known positions.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                                  SELECT mmsi,
                                         name,
                                         speed,
                                         course,
                                         last_seen,
                                         ST_Y(last_pos::geometry) as lat,
                                         ST_X(last_pos::geometry) as lon
                                  FROM vessels
                                  WHERE last_seen < NOW() - (%s * INTERVAL '1 minute')
                                    AND last_seen > NOW() - INTERVAL '24 hours'
                                  ORDER BY last_seen DESC;
                                  """, (minutes,))
                return await cur.fetchall()

    async def get_vessels_in_radius(self, lat: float, lon: float, radius_km: float) -> List[Dict[str, Any]]:
        """
        Retrieves all vessels within a specified distance from a GPS point.

        Uses PostGIS 'ST_DWithin' for efficient spatial indexing and distance calculation.

        Args:
            lat (float): Center latitude.
            lon (float): Center longitude.
            radius_km (float): Search radius in kilometers.

        Returns:
            List[Dict]: Vessels within the defined proximity.
        """
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("""
                                  SELECT mmsi,
                                         name,
                                         type,
                                         speed,
                                         course,
                                         ST_Y(last_pos::geometry) as lat,
                                         ST_X(last_pos::geometry) as lon
                                  FROM vessels
                                  WHERE ST_DWithin(last_pos, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s);
                                  """, (lon, lat, radius_km * 1000))
                return await cur.fetchall()