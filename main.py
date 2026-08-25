"""Entry point JustRunMy.App e local — polling Telegram 24/7."""
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
os.chdir(_root)
_root_str = str(_root)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

if not (_root / "app" / "__init__.py").is_file():
    print(f"ERRO: app/ nao encontrada em {_root}", file=sys.stderr, flush=True)
    print(f"Ficheiros: {[p.name for p in _root.iterdir()]}", file=sys.stderr, flush=True)
    sys.exit(1)

from app.config import get_settings
from app.telegram_polling import main as run_polling

if __name__ == "__main__":
    print("Maratona Coach a arrancar...", flush=True)
    settings = get_settings()
    if settings.showcase_enabled:
        from app.showcase_server import start_showcase_server

        start_showcase_server(port=settings.port)
    run_polling()
