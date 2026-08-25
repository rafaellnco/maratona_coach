"""Processamento de mensagens Telegram — sem dependência de FastAPI (deploy polling)."""

import logging

from sqlmodel import Session

from app.config import get_settings
from app.schemas import CoachResponse
from app.services.coach_agent import CoachAgent
from app.services.telegram_service import TelegramService
from app.services.training_service import get_primary_user, link_telegram_user

logger = logging.getLogger(__name__)


async def process_telegram_message(
    session: Session,
    chat_id: str,
    telegram_user_id: str,
    text: str,
    first_name: str | None,
) -> CoachResponse:
    settings = get_settings()
    telegram = TelegramService(settings)
    user = get_primary_user(session)

    if not telegram.is_user_allowed(telegram_user_id):
        logger.warning("Telegram user não autorizado: %s", telegram_user_id)
        await telegram.send_message(
            chat_id,
            "Este bot é privado. Apenas o proprietário pode usá-lo.",
        )
        return CoachResponse(reply="")

    link_telegram_user(session, user, chat_id, telegram_user_id, first_name)

    if text.startswith("/start"):
        welcome = (
            "Olá! Sou o teu Maratona Coach — treinador de corrida e nutricionista desportivo.\n\n"
            "Podes falar comigo sobre treinos, plano, suplementos, joelhos, hidratação...\n"
            "Exemplos: «corri 10km hoje», «qual é o plano completo?», «como estão os meus joelhos?»"
        )
        await telegram.send_message(chat_id, welcome)
        return CoachResponse(reply=welcome)

    if not settings.anthropic_api_key:
        reply = (
            "Modo demo — configura ANTHROPIC_API_KEY no .env para activar respostas inteligentes."
        )
        await telegram.send_message(chat_id, reply)
        return CoachResponse(reply=reply)

    await telegram.send_typing(chat_id)

    try:
        agent = CoachAgent(settings)
        reply, tools_executed, daily_log_updated = agent.process_message(session, text, user.id)
        await telegram.send_message(chat_id, reply)
        return CoachResponse(
            reply=reply,
            daily_log_updated=daily_log_updated,
            tools_executed=tools_executed,
        )
    except Exception:
        session.rollback()
        logger.exception("Erro ao processar mensagem Telegram")
        error_reply = "Desculpa, tive um problema técnico. Tenta outra vez daqui a instantes."
        await telegram.send_message(chat_id, error_reply)
        return CoachResponse(reply=error_reply)
