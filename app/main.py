import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app import __version__
from app.api.health import router as health_router
from app.api.notifications import router as notifications_router
from app.api.routes import router as api_router
from app.api.telegram import _handle_telegram_webhook, _verify_secret, router as telegram_router
from app.api.webhook import router as webhook_router
from app.config import get_settings
from app.database import create_db_and_tables, get_session, session_scope
from app.log_config import setup_logging
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.seed.initial_data import seed_database
from app.services.telegram_service import TelegramService

setup_logging()
logger = logging.getLogger(__name__)


async def _setup_telegram_webhook() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.telegram_configured:
        logger.info("Telegram: TELEGRAM_BOT_TOKEN não configurado — webhook ignorado.")
        return

    webhook_url = settings.telegram_webhook_url_resolved
    if not webhook_url:
        logger.warning(
            "Telegram webhook não configurado — define PUBLIC_BASE_URL ou TELEGRAM_WEBHOOK_URL."
        )
        return

    telegram = TelegramService(settings)

    me = await telegram.get_me()
    if me.get("ok"):
        username = me.get("result", {}).get("username", "?")
        logger.info("Bot Telegram: @%s (token OK)", username)
    else:
        logger.error("Token Telegram inválido: %s", me)

    result = await telegram.set_webhook(webhook_url)
    if result.get("ok"):
        logger.info("Telegram webhook registado: %s", webhook_url)
    else:
        logger.warning("Falha ao registar Telegram webhook: %s", result)

    info = await telegram.get_webhook_info()
    if info.get("ok"):
        wh = info.get("result", {})
        logger.info(
            "Webhook info: url=%s pending=%s",
            wh.get("url") or "(vazio)",
            wh.get("pending_update_count", 0),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "A iniciar Maratona Coach v%s [%s] — modo %s",
        __version__,
        settings.app_env,
        settings.resolved_telegram_mode,
    )

    if settings.is_production and not settings.telegram_allowed_user_id.strip():
        logger.warning(
            "TELEGRAM_ALLOWED_USER_ID vazio — qualquer pessoa pode usar o bot e consumir a API Claude!"
        )
    elif settings.telegram_allowed_user_id.strip():
        logger.info("Bot privado — só user ID %s autorizado.", settings.telegram_allowed_user_id.strip())

    create_db_and_tables()
    with session_scope() as session:
        seed_database(session)
    logger.info("Base de dados inicializada e seed aplicado.")

    await _setup_telegram_webhook()
    start_scheduler(settings)
    logger.info(
        "Modo webhook activo — scheduler %02d:%02d / %02d:%02d (%s)",
        settings.morning_briefing_hour,
        settings.morning_briefing_minute,
        settings.evening_recovery_hour,
        settings.evening_recovery_minute,
        settings.scheduler_timezone,
    )
    yield
    stop_scheduler()
    logger.info("Aplicação encerrada.")


app = FastAPI(
    title="Maratona Coach API",
    description="AI Telegram Coach — Treinador de Corrida e Nutricionista Desportivo",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(telegram_router)
app.include_router(webhook_router)
app.include_router(api_router)
app.include_router(notifications_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "Maratona Coach",
        "version": __version__,
        "docs": "/docs",
        "webhook": "/webhook/telegram",
    }


@app.post("/")
async def telegram_webhook_root(
    request: Request,
    session: Session = Depends(get_session),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    """Alias — webhook Telegram quando aponta só para o domínio ngrok (POST /)."""
    _verify_secret(x_telegram_bot_api_secret_token)
    return await _handle_telegram_webhook(request, session)
