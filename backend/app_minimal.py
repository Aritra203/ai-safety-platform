"""
Minimal FastAPI app for Render deployment.
Routes load asynchronously in background to avoid startup timeouts.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from backend.config.settings import settings
from backend.config.database import connect_db, disconnect_db, is_db_connected

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route routers (loaded async)
_routers_loaded = False


async def _load_routes_startup(app: FastAPI):
    """Load routes asynchronously after app is running"""
    global _routers_loaded
    
    try:
        logger.info("⏳ Loading ML routes in background...")
        
        from backend.routes.analysis import router as analysis_router
        from backend.routes.fir import router as fir_router
        from backend.routes.analytics import router as analytics_router
        
        app.include_router(analysis_router, tags=["Analysis"])
        app.include_router(fir_router, tags=["FIR"])
        app.include_router(analytics_router, tags=["Analytics"])
        
        _routers_loaded = True
        logger.info("✅ ML routes loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to load ML routes: {e}", exc_info=True)
        _routers_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan - startup is instant"""
    logger.info("🚀 SafeGuard AI starting...")
    
    # Connect to DB in background
    asyncio.create_task(connect_db())
    
    # Load routes in background
    asyncio.create_task(_load_routes_startup(app))
    
    logger.info("✅ Startup complete - listening for requests")
    yield
    logger.info("🛑 Shutting down...")
    await disconnect_db()


app = FastAPI(
    title="SafeGuard AI",
    description="AI-powered cyber safety platform",
    version="3.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# System endpoints (no heavy imports)
@app.get("/", tags=["System"])
async def root():
    """Instant response - app is alive"""
    return {
        "service": "SafeGuard AI",
        "status": "online",
        "version": "3.1.0",
        "routes_ready": _routers_loaded,
    }


@app.get("/health", tags=["System"])
async def health():
    """Health check - instant response"""
    return {
        "status": "ok",
        "service": "SafeGuard AI",
        "database": "connected" if is_db_connected() else "connecting",
        "routes_ready": _routers_loaded,
    }


@app.get("/status", tags=["System"])
async def status():
    """Detailed status"""
    return {
        "app": "SafeGuard AI",
        "version": "3.1.0",
        "port": "listening",
        "database": "connected" if is_db_connected() else "connecting",
        "ml_routes": _routers_loaded,
        "models": "loading in background" if not _routers_loaded else "ready",
    }
