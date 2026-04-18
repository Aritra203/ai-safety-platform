"""Analytics route: GET /analytics"""

import logging
from fastapi import APIRouter, Depends
from models.schemas import AnalyticsResponse
from services.analytics_service import AnalyticsService
from config.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db=Depends(get_db)):
    """Return platform-wide analytics summary."""
    service = AnalyticsService(db)
    return await service.get_summary()
