"""
Async MongoDB connection via Motor.
Exposes `db` as the active database instance throughout the app.
"""

import logging
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
db = None                  
_db_ready = False


async def connect_db() -> None:
    global _client, db, _db_ready
    if _client is None:
        try:
            _client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,                      
                maxPoolSize=10,
                connectTimeoutMS=2000,
            )
            db = _client[settings.MONGODB_DB]
            
                                   
            import asyncio
            try:
                await asyncio.wait_for(_client.admin.command("ping"), timeout=2.0)
                logger.info("✅ MongoDB connected")
                _db_ready = True
                                                           
                asyncio.create_task(_ensure_indexes())
            except asyncio.TimeoutError:
                logger.info("⚠️ MongoDB ping timeout - will retry on first request")
                _db_ready = False
            except Exception as e:
                logger.info(f"⚠️ MongoDB unavailable: {e}")
                _db_ready = False
        except Exception as e:
            logger.info(f"⚠️ Failed to create MongoDB client: {e}")
            _db_ready = False


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
                                                                               
        await connect_db()

    if not _db_ready or db is None:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Start MongoDB or set MONGODB_URI to a reachable instance.",
        )

    return db


async def get_db_optional():
    """Best-effort DB dependency that never raises when Mongo is unavailable."""
    global _db_ready

    if not _db_ready:
        await connect_db()

    if not _db_ready or db is None:
        return None

    return db


def is_db_connected() -> bool:
    return _db_ready
