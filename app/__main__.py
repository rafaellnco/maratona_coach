"""Entry point: python -m app (JustRunMy.App e local)."""

from app.config import get_settings

from app.telegram_polling import main as run_polling





def main() -> None:

    print("Maratona Coach a arrancar...", flush=True)

    settings = get_settings()

    if settings.showcase_enabled:

        from app.showcase_server import start_showcase_server



        start_showcase_server(port=settings.port)

    run_polling()





if __name__ == "__main__":

    main()

