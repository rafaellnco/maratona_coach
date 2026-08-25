"""Integração com Anthropic Claude — agente coach com tool use."""

import json
import logging
from typing import Any

import anthropic
from sqlmodel import Session

from app.config import Settings, get_settings
from app.models import MessageRole, User
from app.services.claude_tools import COACH_TOOLS, build_system_prompt
from app.services.tool_executor import execute_tool
from app.services.training_service import (
    format_daily_log,
    format_week_plan,
    get_current_training_week,
    get_days_until_race,
    get_or_create_daily_log,
    get_primary_user,
    get_recent_logs_summary,
    get_recent_messages,
    get_today_sessions,
    get_user_goal,
    save_message,
)

logger = logging.getLogger(__name__)


class CoachAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = self.settings.anthropic_model

    def _build_context(self, session: Session, user_id: int) -> str:
        user = session.get(User, user_id) if user_id else get_primary_user(session)
        if not user:
            user = get_primary_user(session)

        goal = get_user_goal(session, user_id)
        week = get_current_training_week(session)
        today_log = get_or_create_daily_log(session, user_id)
        today_sessions = get_today_sessions(session)

        user_profile = (
            f"{user.name}, {user.age} anos, {user.gender.value}, "
            f"{user.weight_kg}kg, {user.height_m}m. "
            f"Fumador: {'Sim' if user.is_smoker else 'Não'}. "
            f"Notas: {user.injury_notes or 'Nenhuma'}"
        )
        goal_info = "Sem meta definida."
        if goal:
            pace = f"{goal.target_pace_per_km_seconds // 60}:{goal.target_pace_per_km_seconds % 60:02d}/km"
            goal_info = (
                f"{goal.title} — {goal.distance_km} km a {pace}, "
                f"prova em {goal.target_date}. {goal.description or ''}"
            )

        week_plan = format_week_plan(session, week) if week else "Fora do plano de treino."
        today_str = (
            "\n".join(f"- {s.title}: {s.description}" for s in today_sessions)
            if today_sessions
            else "Dia de descanso (sem treino planeado)."
        )

        return build_system_prompt(
            user_profile=user_profile,
            goal_info=goal_info,
            week_plan=week_plan,
            today_sessions=today_str,
            daily_log=format_daily_log(today_log),
            recent_logs=get_recent_logs_summary(session, user_id),
            days_to_race=get_days_until_race(session, user_id),
        )

    def _history_to_messages(
        self, session: Session, user_id: int
    ) -> list[dict[str, Any]]:
        recent = get_recent_messages(session, user_id, self.settings.conversation_history_limit)
        return [{"role": m.role.value, "content": m.content} for m in recent]

    def process_message(
        self,
        session: Session,
        user_message: str,
        user_id: int | None = None,
    ) -> tuple[str, list[str], bool]:
        user = get_primary_user(session) if user_id is None else session.get(User, user_id)
        if not user or user.id is None:
            raise RuntimeError("Utilizador inválido.")

        uid: int = user.id
        save_message(session, uid, MessageRole.USER, user_message)

        system_prompt = self._build_context(session, uid)
        messages = self._history_to_messages(session, uid)
        messages.append({"role": "user", "content": user_message})

        tools_executed: list[str] = []
        daily_log_updated = False
        max_iterations = 6

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                tools=COACH_TOOLS,
                messages=messages,  # type: ignore[arg-type]
            )

            if response.stop_reason == "tool_use":
                assistant_content: list[dict[str, Any]] = []
                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        assistant_content.append(
                            {
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            }
                        )
                        result = execute_tool(session, uid, block.name, block.input)  # type: ignore[arg-type]
                        tools_executed.append(block.name)
                        if block.name == "update_daily_log" and result.get("success"):
                            daily_log_updated = True
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False),
                            }
                        )

                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})
                continue

            reply_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    reply_text += block.text

            if not reply_text.strip():
                reply_text = "Recebi a tua mensagem. Como posso ajudar com o teu treino hoje?"

            save_message(session, uid, MessageRole.ASSISTANT, reply_text)
            session.commit()
            return reply_text, tools_executed, daily_log_updated

        fallback = "Desculpa, tive dificuldade a processar. Podes repetir?"
        save_message(session, uid, MessageRole.ASSISTANT, fallback)
        session.commit()
        return fallback, tools_executed, daily_log_updated

    def generate_proactive_message(
        self,
        session: Session,
        prompt: str,
        user_id: int | None = None,
    ) -> str:
        """Gera mensagem proactiva (notificações) sem tool use."""
        user = get_primary_user(session) if user_id is None else session.get(User, user_id)
        if not user or user.id is None:
            raise RuntimeError("Utilizador inválido.")

        system_prompt = self._build_context(session, user.id)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )

        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        return text.strip()
