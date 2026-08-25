from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    database_url: str = "sqlite:///./maratona_coach.db"

    # Telegram (canal principal)
    telegram_bot_token: str = ""
    # auto = webhook se PUBLIC_BASE_URL/TELEGRAM_WEBHOOK_URL; senão polling (local)
    telegram_mode: str = "auto"
    public_base_url: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""
    telegram_allowed_user_id: str = ""
    cron_secret: str = ""

    # WhatsApp / Twilio (legado — opcional)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    user_whatsapp_number: str = ""

    scheduler_timezone: str = "Europe/Lisbon"
    morning_briefing_hour: int = 9
    morning_briefing_minute: int = 0
    lunch_supplements_hour: int = 14
    lunch_supplements_minute: int = 0
    run_day_reminder_hour: int = 17
    run_day_reminder_minute: int = 0
    dinner_supplements_hour: int = 21
    dinner_supplements_minute: int = 30
    evening_recovery_hour: int = 22
    evening_recovery_minute: int = 30

    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000
    showcase_enabled: bool = True

    conversation_history_limit: int = 20

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token)

    @property
    def telegram_webhook_url_resolved(self) -> str:
        explicit = self.telegram_webhook_url.strip().rstrip("/")
        if explicit:
            return explicit
        base = self.public_base_url.strip().rstrip("/")
        if base:
            return f"{base}/webhook/telegram"
        return ""

    @property
    def resolved_telegram_mode(self) -> str:
        mode = self.telegram_mode.lower().strip()
        if mode in ("polling", "webhook"):
            return mode
        return "webhook" if self.telegram_webhook_url_resolved else "polling"

    @property
    def twilio_configured(self) -> bool:
        return bool(
            self.twilio_account_sid
            and self.twilio_auth_token
            and self.user_whatsapp_number
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
