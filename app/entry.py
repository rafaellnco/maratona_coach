"""Entry point unificado — polling (local) ou webhook (produção)."""

import logging
import sys

from app.config import get_settings

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    mode = settings.resolved_telegram_mode
    logger.info(
        "Maratona Coach — modo Telegram: %s (APP_ENV=%s)",
        mode,
        settings.app_env,
    )

    if mode == "webhook":
        run_webhook_server()
    else:
        run_polling_server()


def run_webhook_server() -> None:
    import uvicorn

    from app.log_config import setup_logging

    settings = get_settings()
    setup_logging()

    webhook_url = settings.telegram_webhook_url_resolved
    if not webhook_url:
        logger.error(
            "Modo webhook activo mas PUBLIC_BASE_URL / TELEGRAM_WEBHOOK_URL vazio. "
            "No JustRunMy: Settings → copia o URL público → PUBLIC_BASE_URL=https://..."
        )
        sys.exit(1)

    logger.info("Webhook URL: %s", webhook_url)
    logger.info("A arrancar FastAPI na porta %s...", settings.port)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


def run_polling_server() -> None:
    from app.log_config import setup_logging
    from app.showcase_server import start_showcase_server
    from app.telegram_polling import main as run_polling

    setup_logging()
    settings = get_settings()
    print("Maratona Coach a arrancar...", flush=True)

    if settings.showcase_enabled:
        start_showcase_server(port=settings.port)

    run_polling()


if __name__ == "__main__":
    main()
