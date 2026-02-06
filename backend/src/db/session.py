import asyncio
import psycopg
import logging

# Logger configuration
logger = logging.getLogger(__name__)


async def wait_for_db(db_url: str):
    """
    Implements a health-check retry loop to ensure database readiness.

    This is critical in containerized environments (Docker) to prevent
    application crashes during the initial startup phase when the
    database might still be initializing.

    Args:
        db_url (str): Connection string for the PostgreSQL/PostGIS database.

    Returns:
        bool: True if connection is successfully established.

    Raises:
        Exception: If the database remains unreachable after 10 attempts.
    """
    max_retries = 10
    retry_interval = 2  # seconds

    for i in range(max_retries):
        try:
            # Attempt a direct connection to verify DB availability
            async with await psycopg.AsyncConnection.connect(db_url) as conn:
                logger.info("✅ Database connection established: PostGIS is ready.")
                return True
        except Exception:
            logger.info(
                f"⏳ Waiting for database readiness... (Attempt {i + 1}/{max_retries})"
            )
            await asyncio.sleep(retry_interval)

    # Final failure state if DB doesn't respond
    error_msg = "❌ Critical Error: Could not connect to the database after multiple attempts."
    logger.critical(error_msg)
    raise Exception(error_msg)