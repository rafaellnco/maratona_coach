"""APScheduler — notificações automáticas."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Settings, get_settings
from app.database import session_scope
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_morning_briefing() -> None:
    logger.info("Executando briefing matinal...")
    with session_scope() as session:
        service = NotificationService()
        await service.morning_briefing(session)


async def _run_lunch_supplements() -> None:
    logger.info("Executando lembrete suplementos (almoço)...")
    with session_scope() as session:
        service = NotificationService()
        await service.lunch_supplements(session)


async def _run_dinner_supplements() -> None:
    logger.info("Executando lembrete suplementos (jantar)...")
    with session_scope() as session:
        service = NotificationService()
        await service.dinner_supplements(session)


async def _run_run_day_reminder() -> None:
    logger.info("Executando lembrete dia de treino...")
    with session_scope() as session:
        service = NotificationService()
        await service.run_day_reminder(session)


async def _run_evening_recovery() -> None:
    logger.info("Executando lembrete de recovery...")
    with session_scope() as session:
        service = NotificationService()
        await service.evening_recovery(session)


def start_scheduler(settings: Settings | None = None) -> AsyncIOScheduler:
    cfg = settings or get_settings()

    jobs = [
        (
            "morning_briefing",
            _run_morning_briefing,
            cfg.morning_briefing_hour,
            cfg.morning_briefing_minute,
        ),
        (
            "lunch_supplements",
            _run_lunch_supplements,
            cfg.lunch_supplements_hour,
            cfg.lunch_supplements_minute,
        ),
        (
            "run_day_reminder",
            _run_run_day_reminder,
            cfg.run_day_reminder_hour,
            cfg.run_day_reminder_minute,
        ),
        (
            "dinner_supplements",
            _run_dinner_supplements,
            cfg.dinner_supplements_hour,
            cfg.dinner_supplements_minute,
        ),
        (
            "evening_recovery",
            _run_evening_recovery,
            cfg.evening_recovery_hour,
            cfg.evening_recovery_minute,
        ),
    ]

    for job_id, func, hour, minute in jobs:
        scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute, timezone=cfg.scheduler_timezone),
            id=job_id,
            replace_existing=True,
            misfire_grace_time=300,
        )

    if not scheduler.running:
        scheduler.start()
        logger.info(
            "Scheduler iniciado — 09:00 briefing, 14:00 suplementos almoço, "
            "17:00 treino, 21:30 suplementos jantar, 22:30 recovery (%s)",
            cfg.scheduler_timezone,
        )

    return scheduler


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler parado.")
