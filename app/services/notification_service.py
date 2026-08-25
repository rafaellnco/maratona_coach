"""Serviço de notificações automáticas via Telegram."""

import logging
from datetime import date, datetime

from sqlmodel import Session

from app.config import Settings, get_settings
from app.models import NotificationLog
from app.services.coach_agent import CoachAgent
from app.services.telegram_service import TelegramService
from app.services.training_service import (
    format_daily_log,
    get_or_create_daily_log,
    get_primary_user,
    get_today_sessions,
    is_training_day,
)

logger = logging.getLogger(__name__)

MORNING_PROMPT = """Gera a mensagem de briefing matinal (09:00) para Telegram.
Inclui:
1. Treino(s) planeados para hoje — se for dia de corrida, destaca com energia (distância, tipo, hora sugerida)
2. Meta de água do dia (3.5L treino / 2.5L descanso)
3. Lembrete breve das regras de ouro relevantes para hoje
Tom: motivador, directo, PT-PT. Texto simples (sem markdown). Máximo 150 palavras."""

LUNCH_SUPPLEMENTS_PROMPT = """Gera lembrete pós-almoço (~14:00) para Telegram.
Pergunta de forma directa se já tomou após o almoço:
- Ómega-3
- Creatina (3 a 5 g)
Pede resposta curta (ex: «sim, os dois» ou «ainda não»).
Tom: amigável, PT-PT. Texto simples. Máximo 80 palavras."""

DINNER_SUPPLEMENTS_PROMPT = """Gera lembrete pós-jantar (~21:30) para Telegram.
Pergunta se já tomou com o jantar:
- Ómega-3
- Creatina (se ainda não registaste hoje)
Referencia que o Magnésio Solgar é mais tarde (~22:30).
Tom: amigável, PT-PT. Texto simples. Máximo 80 palavras."""

RUN_DAY_PROMPT = """Gera lembrete de foco no treino (~17:00) para Telegram — só em dias com treino planeado.
Inclui:
1. Nome/descrição do treino de hoje
2. Motivação curta para não adiar
3. Meta de água até agora
Tom: energético mas não agressivo, PT-PT. Texto simples. Máximo 100 palavras."""

EVENING_PROMPT = """Gera a mensagem de recovery noturno (22:30) para Telegram.
Inclui:
1. Lembrete Citrato de Magnésio Solgar
2. Pergunta sobre estado dos joelhos (escala 0-10)
3. Breve check-in de recovery (sono, hidratação do dia)
Tom: calmo, de cuidado, PT-PT. Texto simples (sem markdown). Máximo 120 palavras."""


class NotificationService:
    def __init__(
        self,
        settings: Settings | None = None,
        coach: CoachAgent | None = None,
        telegram: TelegramService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.coach = coach or CoachAgent(self.settings)
        self.telegram = telegram or TelegramService(self.settings)

    def _log_notification(
        self,
        session: Session,
        user_id: int,
        notification_type: str,
        message: str,
        delivery_status: str,
    ) -> NotificationLog:
        entry = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_for=datetime.utcnow(),
            sent_at=datetime.utcnow(),
            message_content=message,
            delivery_status=delivery_status,
        )
        session.add(entry)
        session.flush()
        return entry

    async def _deliver_telegram(self, session: Session, message: str) -> str:
        user = get_primary_user(session)
        if not self.settings.telegram_configured:
            logger.info("Telegram não configurado — notificação simulada:\n%s", message)
            return "simulated"

        if not user.telegram_chat_id:
            logger.info(
                "Utilizador sem telegram_chat_id — envia /start ao bot primeiro. Simulado:\n%s",
                message,
            )
            return "simulated"

        sent = await self.telegram.send_message(user.telegram_chat_id, message)
        return "sent" if sent else "failed"

    async def send_notification(
        self,
        session: Session,
        notification_type: str,
        prompt: str,
    ) -> NotificationLog:
        user = get_primary_user(session)
        if user.id is None:
            raise RuntimeError("Utilizador sem ID.")

        if self.settings.anthropic_api_key:
            message = self.coach.generate_proactive_message(session, prompt, user.id)
            delivery = await self._deliver_telegram(session, message)
        else:
            message = self._fallback_message(session, notification_type, user.id)
            delivery = "fallback"
            logger.info("[%s] Fallback (sem API key):\n%s", notification_type, message)

        return self._log_notification(session, user.id, notification_type, message, delivery)

    def _fallback_message(self, session: Session, notification_type: str, user_id: int) -> str:
        today = date.today()
        training = is_training_day(session, today)
        sessions = get_today_sessions(session)
        log = get_or_create_daily_log(session, user_id, today)
        water_target = log.water_target_liters or (3.5 if training else 2.5)

        if notification_type == "morning_briefing":
            if sessions:
                treino = sessions[0].title
                return (
                    f"Bom dia! Hoje é dia de treino: {treino}. Meta de água: {water_target}L. "
                    "Bons treinos — lembra-te: sem tabaco 2h antes/depois do exercício."
                )
            return (
                f"Bom dia! Dia de descanso. Meta de água: {water_target}L. "
                "Aproveita para recuperar — joelhos a agradecer."
            )

        if notification_type == "lunch_supplements":
            return (
                "Almoço feito? Já tomaste Ómega-3 e Creatina (3–5g)? "
                "Responde «sim, os dois» ou «ainda não» — registo no teu log."
            )

        if notification_type == "dinner_supplements":
            return (
                "Jantar feito? Ómega-3 e Creatina — já tomaste? "
                "O Magnésio Solgar vem às 22:30. Responde sim/não."
            )

        if notification_type == "run_day_reminder":
            if sessions:
                treino = sessions[0].title
                if log.training_completed:
                    return (
                        f"Boa! Treino de hoje ({treino}) já registado. "
                        f"Água meta: {water_target}L — mantém a hidratação."
                    )
                return (
                    f"Lembrete: hoje tens {treino}. Ainda dá tempo — mantém o foco! "
                    f"Meta de água: {water_target}L."
                )
            return "Lembrete de treino — consulta o plano de hoje."

        return (
            f"Boa noite! Hora do Magnésio Solgar. "
            f"Como estão os joelhos hoje? Registo: {format_daily_log(log)}"
        )

    async def morning_briefing(self, session: Session) -> NotificationLog:
        return await self.send_notification(session, "morning_briefing", MORNING_PROMPT)

    async def lunch_supplements(self, session: Session) -> NotificationLog:
        return await self.send_notification(session, "lunch_supplements", LUNCH_SUPPLEMENTS_PROMPT)

    async def dinner_supplements(self, session: Session) -> NotificationLog:
        return await self.send_notification(session, "dinner_supplements", DINNER_SUPPLEMENTS_PROMPT)

    async def run_day_reminder(self, session: Session) -> NotificationLog | None:
        today = date.today()
        if not is_training_day(session, today):
            logger.info("run_day_reminder ignorado — não é dia de treino.")
            return None
        return await self.send_notification(session, "run_day_reminder", RUN_DAY_PROMPT)

    async def evening_recovery(self, session: Session) -> NotificationLog:
        return await self.send_notification(session, "evening_recovery", EVENING_PROMPT)
