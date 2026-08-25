"""Trigger manual de notificações (útil para testes e cron externo)."""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from app.config import get_settings
from app.database import get_session
from app.schemas import SimulatedNotification
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _verify_cron_secret(x_cron_secret: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.cron_secret.strip()
    if expected and x_cron_secret != expected:
        raise HTTPException(status_code=403, detail="Cron secret inválido.")


@router.post("/trigger/morning", response_model=SimulatedNotification)
async def trigger_morning(
    session: Session = Depends(get_session),
    _: None = Depends(_verify_cron_secret),
) -> SimulatedNotification:
    service = NotificationService()
    log = await service.morning_briefing(session)
    session.commit()
    return SimulatedNotification(
        notification_type=log.notification_type,
        message=log.message_content,
        scheduled_for=log.scheduled_for,
        delivery_status=log.delivery_status,
    )


@router.post("/trigger/evening", response_model=SimulatedNotification)
async def trigger_evening(
    session: Session = Depends(get_session),
    _: None = Depends(_verify_cron_secret),
) -> SimulatedNotification:
    service = NotificationService()
    log = await service.evening_recovery(session)
    session.commit()
    return SimulatedNotification(
        notification_type=log.notification_type,
        message=log.message_content,
        scheduled_for=log.scheduled_for,
        delivery_status=log.delivery_status,
    )
