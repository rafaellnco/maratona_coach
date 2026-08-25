import logging



from fastapi import APIRouter, Depends, Header, HTTPException, Request

from sqlmodel import Session



from app.config import get_settings

from app.database import get_session

from app.services.telegram_handler import process_telegram_message

from app.services.telegram_service import TelegramService



logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["telegram"])





def _verify_secret(x_telegram_bot_api_secret_token: str | None = Header(default=None)) -> None:

    settings = get_settings()

    expected = settings.telegram_webhook_secret.strip()

    if expected and x_telegram_bot_api_secret_token != expected:

        raise HTTPException(status_code=403, detail="Webhook secret inválido.")





async def _handle_telegram_webhook(request: Request, session: Session) -> dict[str, bool]:

    data = await request.json()

    telegram = TelegramService()

    incoming = telegram.parse_update(data)



    if not incoming:

        return {"ok": True}



    await process_telegram_message(

        session,

        incoming.chat_id,

        incoming.telegram_user_id,

        incoming.text,

        incoming.first_name,

    )

    session.commit()

    return {"ok": True}





@router.post("/telegram/register")

async def register_telegram_webhook() -> dict:

    """Regista manualmente o webhook (útil após alterar .env ou ngrok)."""

    get_settings.cache_clear()

    settings = get_settings()

    webhook_url = settings.telegram_webhook_url_resolved

    if not settings.telegram_configured or not webhook_url:

        raise HTTPException(

            status_code=400,

            detail="Configura TELEGRAM_BOT_TOKEN e PUBLIC_BASE_URL (ou TELEGRAM_WEBHOOK_URL) no .env",

        )

    telegram = TelegramService(settings)

    result = await telegram.set_webhook(webhook_url)

    info = await telegram.get_webhook_info()

    return {"set_webhook": result, "webhook_info": info.get("result", {})}





@router.post("/telegram")

async def telegram_webhook(

    request: Request,

    session: Session = Depends(get_session),

    _: None = Depends(_verify_secret),

) -> dict[str, bool]:

    """Webhook Telegram Bot API."""

    return await _handle_telegram_webhook(request, session)


