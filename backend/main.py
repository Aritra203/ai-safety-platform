"""
SafeGuard AI — FastAPI Backend
Main application entry point with all routes, middleware, and startup logic.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project-root modules (e.g., ai_services/) are importable when running from backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config.settings import settings
from backend.config.database import connect_db, disconnect_db, is_db_connected

# Import routes with error handling
try:
    from backend.routes.analysis import router as analysis_router
except ImportError as e:
    logger.warning(f"⚠️ Analysis router import failed: {e}. Analysis endpoints disabled.")
    analysis_router = None

try:
    from backend.routes.fir import router as fir_router
except ImportError as e:
    logger.warning(f"⚠️ FIR router import failed: {e}. FIR endpoints disabled.")
    fir_router = None

try:
    from backend.routes.analytics import router as analytics_router
except ImportError as e:
    logger.warning(f"⚠️ Analytics router import failed: {e}. Analytics endpoints disabled.")
    analytics_router = None

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SafeGuard AI starting up...")
    try:
        # Connect to MongoDB with timeout
        try:
            await asyncio.wait_for(connect_db(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️ MongoDB connection timed out. API will work in degraded mode.")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}. API will work in degraded mode.")
        
        if is_db_connected():
            logger.info("✅ MongoDB connected")
        else:
            logger.warning("⚠️ MongoDB not connected. API is running in degraded mode.")
        
        logger.info("✅ Startup complete - API ready for requests")
    except Exception as e:
        logger.warning(f"⚠️ Startup warning (non-fatal): {e}")
    
    yield
    
    try:
        logger.info("🛑 SafeGuard AI shutting down...")
        await disconnect_db()
        logger.info("✅ Cleanup complete")
    except Exception as e:
        logger.warning(f"⚠️ Shutdown warning: {e}")


# ── App factory ──────────────────────────────────────────────────
app = FastAPI(
    title="SafeGuard AI",
    description="AI-powered cyber safety & FIR generation platform",
    version="3.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ──────────────────────────────────────────────────────
if analysis_router:
    app.include_router(analysis_router, tags=["Analysis"])
if fir_router:
    app.include_router(fir_router, tags=["FIR"])
if analytics_router:
    app.include_router(analytics_router, tags=["Analytics"])


# ── Health check ─────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    db_ok = is_db_connected()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "3.1.0",
        "service": "SafeGuard AI",
        "database": "connected" if db_ok else "unavailable",
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint - quick health check"""
    return {
        "service": "SafeGuard AI",
        "status": "online",
        "version": "3.1.0",
        "docs": "/docs",
    }
