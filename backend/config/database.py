"""
Async MongoDB connection via Motor.
Exposes `db` as the active database instance throughout the app.
"""

import logging
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
db = None  # set on startup
_db_ready = False


async def connect_db() -> None:
    global _client, db, _db_ready
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=20,
        )
    db = _client[settings.MONGODB_DB]

    try:
        # Verify connection
        await _client.admin.command("ping")
        logger.info("MongoDB connected: %s / %s", settings.MONGODB_URI, settings.MONGODB_DB)

        # Ensure indexes
        await _ensure_indexes()
        _db_ready = True
    except Exception as e:
        _db_ready = False
        logger.warning("MongoDB unavailable at startup (%s). API will run in degraded mode.", e)


async def disconnect_db() -> None:
    global _client, db, _db_ready
    if _client:
        _client.close()
        _client = None
    db = None
    _db_ready = False
    logger.info("MongoDB disconnected")


async def _ensure_indexes() -> None:
    """Create indexes for performance and uniqueness."""
    if db is None:
        return

    await db.analyses.create_index("id", unique=True)
    await db.analyses.create_index("created_at")
    await db.analyses.create_index("risk_level")

    await db.fir_reports.create_index("fir_id", unique=True)
    await db.fir_reports.create_index("analysis_id")
    await db.fir_reports.create_index("created_at")

    logger.info("MongoDB indexes ensured")


async def get_db():
    """Dependency-injection helper for FastAPI routes."""
    global _db_ready

    if not _db_ready:
        # Best-effort reconnect for requests that arrive after DB comes online.
        await connect_db()

    if not _db_ready or db is None:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Start MongoDB or set MONGODB_URI to a reachable instance.",
        )

    return db


def is_db_connected() -> bool:
    return _db_ready
