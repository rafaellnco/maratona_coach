"""Servidor HTTP estático para a página showcase (JustRunMy.App HTTPS)."""

import logging
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def start_showcase_server(host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer | None:
    if not DOCS_DIR.is_dir():
        logger.warning("Pasta docs/ não encontrada — showcase indisponível.")
        return None

    handler = partial(SimpleHTTPRequestHandler, directory=str(DOCS_DIR))
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="showcase-http",
    )
    thread.start()
    logger.info(
        "Showcase disponível em http://%s:%s/ — mapeia a porta %s no JustRunMy.App para obter HTTPS público.",
        host,
        port,
        port,
    )
    return server
