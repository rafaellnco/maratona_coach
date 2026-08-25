"""Entry point FPS.ms — usar PY_FILE=bot.py (NAO app.py, conflita com pasta app/)."""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.config import get_settings
from app.telegram_polling import main as run_polling

if __name__ == "__main__":
    print("Maratona Coach a arrancar...", flush=True)
    settings = get_settings()
    if settings.showcase_enabled:
        from app.showcase_server import start_showcase_server

        start_showcase_server(port=settings.port)
    run_polling()
