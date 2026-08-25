"""Telegram long-polling — funciona 24/7 sem URL pública (ideal para hosts free)."""

import asyncio
import logging
from pathlib import Path

import httpx
from sqlmodel import Session

from app.config import get_settings
from app.database import engine, create_db_and_tables, session_scope
from app.log_config import setup_logging
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.seed.initial_data import seed_database
from app.services.telegram_service import TELEGRAM_API, TelegramService
from app.services.telegram_handler import process_telegram_message

setup_logging()
logger = logging.getLogger(__name__)


def _ensure_data_dir() -> None:
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///./"):
        rel = settings.database_url.replace("sqlite:///./", "")
        Path(rel).parent.mkdir(parents=True, exist_ok=True)
    elif settings.database_url.startswith("sqlite:////data"):
        Path("/data").mkdir(parents=True, exist_ok=True)


async def delete_webhook(token: str) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(TELEGRAM_API.format(token=token, method="deleteWebhook"))
        logger.info("deleteWebhook: %s", response.json())


async def poll_forever() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    if settings.resolved_telegram_mode == "webhook":
        raise RuntimeError(
            "Modo webhook activo — usa: python -m app.entry (ou uvicorn app.main:app). "
            "Polling só em local com TELEGRAM_MODE=polling ou sem PUBLIC_BASE_URL."
        )
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado.")

    if settings.is_production and not settings.telegram_allowed_user_id.strip():
        logger.warning(
            "TELEGRAM_ALLOWED_USER_ID vazio — qualquer pessoa pode usar o bot e consumir a API Claude!"
        )
    elif settings.telegram_allowed_user_id.strip():
        logger.info("Bot privado — só user ID %s autorizado.", settings.telegram_allowed_user_id.strip())

    _ensure_data_dir()
    create_db_and_tables()
    with session_scope() as session:
        seed_database(session)

    await delete_webhook(settings.telegram_bot_token)

    async with httpx.AsyncClient(timeout=15.0) as client:
        me = await client.get(TELEGRAM_API.format(token=settings.telegram_bot_token, method="getMe"))
        me_data = me.json()
        if me_data.get("ok"):
            bot_user = me_data["result"].get("username", "?")
            logger.info("Bot Telegram: @%s (token OK)", bot_user)
        else:
            logger.error("Token Telegram inválido: %s", me_data)

    start_scheduler(settings)
    logger.info("Modo polling activo — bot online 24/7 (sem webhook).")

    telegram = TelegramService(settings)
    offset: int | None = None
    url = TELEGRAM_API.format(token=settings.telegram_bot_token, method="getUpdates")

    try:
        while True:
            try:
                params: dict[str, int | str] = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset

                async with httpx.AsyncClient(timeout=65.0) as client:
                    response = await client.get(url, params=params)
                    data = response.json()

                if not data.get("ok"):
                    desc = str(data.get("description", data))
                    if "Conflict" in desc or "terminated by other getUpdates" in desc:
                        logger.error(
                            "CONFLITO polling — para o bot no PC, JustRunMy e FPS antigo. %s",
                            desc,
                        )
                    else:
                        logger.error("getUpdates error: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    incoming = telegram.parse_update(update)
                    if not incoming:
                        continue

                    logger.info("Mensagem de user_id=%s: %s", incoming.telegram_user_id, incoming.text[:80])

                    with Session(engine) as session:
                        try:
                            await process_telegram_message(
                                session,
                                incoming.chat_id,
                                incoming.telegram_user_id,
                                incoming.text,
                                incoming.first_name,
                            )
                            session.commit()
                        except Exception:
                            session.rollback()
                            logger.exception("Erro ao processar update %s", update.get("update_id"))

            except Exception:
                logger.exception("Erro no polling loop")
                await asyncio.sleep(5)
    finally:
        stop_scheduler()


def main() -> None:
    asyncio.run(poll_forever())


if __name__ == "__main__":
    main()
