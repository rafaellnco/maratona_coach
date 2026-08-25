import logging
from typing import Any

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.schemas import CoachResponse, TwilioWhatsAppPayload, WhatsAppGenericPayload
from app.services.coach_agent import CoachAgent
from app.services.training_service import get_primary_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


def _twiml_response(message: str) -> Response:
    escaped = (
        message.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escaped}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


@router.post("/whatsapp", response_model=CoachResponse)
async def whatsapp_generic(
    payload: WhatsAppGenericPayload,
    session: Session = Depends(get_session),
) -> CoachResponse:
    """Webhook genérico JSON para integrações WhatsApp."""
    return await _handle_message(session, payload.body, payload.from_number)


@router.post("/whatsapp/twilio")
async def whatsapp_twilio(
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    """Webhook Twilio — aceita form-urlencoded e responde TwiML."""
    form = await request.form()
    data = dict(form)
    try:
        payload = TwilioWhatsAppPayload.model_validate(data)
    except Exception as exc:
        logger.warning("Payload Twilio inválido: %s", exc)
        raise HTTPException(status_code=422, detail="Payload Twilio inválido") from exc

    result = await _handle_message(session, payload.Body, payload.From)
    return _twiml_response(result.reply)


@router.post("/whatsapp/raw", response_model=None)
async def whatsapp_raw(
    request: Request,
    session: Session = Depends(get_session),
) -> CoachResponse | Response:
    """
    Webhook flexível — deteta automaticamente Twilio (form) ou JSON genérico.
    """
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        data = dict(form)
        payload = TwilioWhatsAppPayload.model_validate(data)
        result = await _handle_message(session, payload.Body, payload.From)
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            return result
        return _twiml_response(result.reply)

    body: dict[str, Any] = await request.json()
    if "Body" in body and "From" in body:
        payload = TwilioWhatsAppPayload.model_validate(body)
        message_body = payload.Body
        from_number = payload.From
    else:
        payload = WhatsAppGenericPayload.model_validate(body)
        message_body = payload.body
        from_number = payload.from_number

    return await _handle_message(session, message_body, from_number)


async def _handle_message(
    session: Session,
    message_body: str,
    from_number: str,
) -> CoachResponse:
    if not message_body.strip():
        raise HTTPException(status_code=400, detail="Mensagem vazia.")

    settings = get_settings()
    user = get_primary_user(session)

    if user.phone_number is None:
        user.phone_number = from_number
        session.add(user)
        session.flush()
    elif user.phone_number != from_number and settings.app_env == "production":
        logger.warning("Número não autorizado: %s", from_number)

    if not settings.anthropic_api_key:
        reply = (
            "Olá! O coach está em modo demo (sem ANTHROPIC_API_KEY). "
            "Configura a chave API para activar respostas inteligentes."
        )
        return CoachResponse(reply=reply)

    try:
        agent = CoachAgent(settings)
        reply, tools_executed, daily_log_updated = agent.process_message(
            session, message_body.strip(), user.id
        )
        return CoachResponse(
            reply=reply,
            daily_log_updated=daily_log_updated,
            tools_executed=tools_executed,
        )
    except anthropic.APIError as exc:
        logger.exception("Erro Anthropic API")
        raise HTTPException(status_code=502, detail=f"Erro Claude API: {exc}") from exc
    except Exception as exc:
        logger.exception("Erro ao processar mensagem")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
