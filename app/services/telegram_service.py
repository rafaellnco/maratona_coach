"""Integração com Telegram Bot API."""

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE_LENGTH = 4096


@dataclass(frozen=True)
class TelegramIncomingMessage:
    chat_id: str
    telegram_user_id: str
    text: str
    first_name: str | None = None
    username: str | None = None


class TelegramService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _token(self) -> str:
        return self.settings.telegram_bot_token

    def _url(self, method: str) -> str:
        return TELEGRAM_API.format(token=self._token, method=method)

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Remove markdown que o coach possa gerar — Telegram fica em texto simples."""
        cleaned = text.replace("**", "").replace("__", "").replace("`", "")
        cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()

    @staticmethod
    def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
        if len(text) <= max_length:
            return [text]

        chunks: list[str] = []
        remaining = text
        while remaining:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break
            split_at = remaining.rfind("\n\n", 0, max_length)
            if split_at < max_length // 2:
                split_at = remaining.rfind("\n", 0, max_length)
            if split_at < max_length // 2:
                split_at = remaining.rfind(" ", 0, max_length)
            if split_at <= 0:
                split_at = max_length
            chunks.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()
        return [c for c in chunks if c]

    def parse_update(self, data: dict[str, Any]) -> TelegramIncomingMessage | None:
        message = data.get("message") or data.get("edited_message")
        if not message:
            return None

        text = message.get("text") or message.get("caption")
        if not text or not str(text).strip():
            return None

        chat = message.get("chat") or {}
        from_user = message.get("from") or {}
        chat_id = chat.get("id")
        user_id = from_user.get("id")

        if chat_id is None or user_id is None:
            return None

        return TelegramIncomingMessage(
            chat_id=str(chat_id),
            telegram_user_id=str(user_id),
            text=str(text).strip(),
            first_name=from_user.get("first_name"),
            username=from_user.get("username"),
        )

    def is_user_allowed(self, telegram_user_id: str) -> bool:
        allowed = self.settings.telegram_allowed_user_id.strip()
        if not allowed:
            return True
        return telegram_user_id == allowed

    async def send_message(self, chat_id: str, text: str) -> bool:
        if not self._token:
            logger.warning("TELEGRAM_BOT_TOKEN não configurado.")
            return False

        safe_text = self.sanitize_text(text)
        parts = self.split_message(safe_text)
        ok = True

        async with httpx.AsyncClient(timeout=30.0) as client:
            for part in parts:
                response = await client.post(
                    self._url("sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": part,
                        "disable_web_page_preview": True,
                    },
                )
                if response.status_code >= 400:
                    logger.error("Telegram sendMessage error %s: %s", response.status_code, response.text)
                    ok = False
        return ok

    async def send_typing(self, chat_id: str) -> None:
        if not self._token:
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                self._url("sendChatAction"),
                json={"chat_id": chat_id, "action": "typing"},
            )

    async def get_me(self) -> dict[str, Any]:
        if not self._token:
            return {"ok": False, "description": "Token não configurado"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._url("getMe"))
            return response.json()

    async def set_webhook(self, webhook_url: str) -> dict[str, Any]:
        if not self._token:
            return {"ok": False, "description": "Token não configurado"}

        payload: dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "edited_message"],
        }
        if self.settings.telegram_webhook_secret:
            payload["secret_token"] = self.settings.telegram_webhook_secret

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._url("setWebhook"), json=payload)
            return response.json()

    async def get_webhook_info(self) -> dict[str, Any]:
        if not self._token:
            return {"ok": False, "description": "Token não configurado"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._url("getWebhookInfo"))
            return response.json()

    async def delete_webhook(self) -> dict[str, Any]:
        if not self._token:
            return {"ok": False, "description": "Token não configurado"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self._url("deleteWebhook"))
            return response.json()
