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

# Import routes lazily (routes are imported only when first request comes in)
# This avoids loading heavy ML models during startup
analysis_router = None
fir_router = None
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
    """Minimal startup - return immediately"""
    logger.info("🚀 SafeGuard AI starting...")
    
    # Try to connect to DB in background (don't block)
    import asyncio
    asyncio.create_task(connect_db())
    
    logger.info("✅ Ready (models load on first request)")
    yield
    
    # Cleanup
    try:
        await disconnect_db()
    except Exception:
        pass


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


# ── Lazy route loading on first request ───────────────────────────
async def _load_routes_once():
    """Load routes lazily on first request (don't block startup)"""
    global analysis_router, fir_router, analytics_router
    
    if analysis_router is None:
        logger.info("⏳ Loading analysis routes...")
        try:
            from backend.routes.analysis import router as analysis_router_import
            analysis_router = analysis_router_import
            app.include_router(analysis_router, tags=["Analysis"])
            logger.info("✅ Analysis routes loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load analysis routes: {e}")
    
    if fir_router is None:
        logger.info("⏳ Loading FIR routes...")
        try:
            from backend.routes.fir import router as fir_router_import
            fir_router = fir_router_import
            app.include_router(fir_router, tags=["FIR"])
            logger.info("✅ FIR routes loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load FIR routes: {e}")
    
    if analytics_router is None:
        logger.info("⏳ Loading analytics routes...")
        try:
            from backend.routes.analytics import router as analytics_router_import
            analytics_router = analytics_router_import
            app.include_router(analytics_router, tags=["Analytics"])
            logger.info("✅ Analytics routes loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load analytics routes: {e}")


# Add startup event that loads routes in background
@app.on_event("startup")
async def load_routes_background():
    """Load routes in background after app is running"""
    import asyncio
    asyncio.create_task(_load_routes_once())
