import logging

from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.schemas import HealthResponse
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.app_env,
    )


@router.get("/health/telegram")
async def telegram_health() -> dict:
    settings = get_settings()
    payload: dict = {
        "telegram_mode": settings.resolved_telegram_mode,
        "webhook_url_configured": settings.telegram_webhook_url_resolved or None,
        "bot_configured": settings.telegram_configured,
    }
    if settings.telegram_configured:
        telegram = TelegramService(settings)
        info = await telegram.get_webhook_info()
        if info.get("ok"):
            payload["webhook_info"] = info.get("result", {})
    return payload
