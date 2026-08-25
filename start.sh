#!/bin/sh
# JustRunMy.App — arranque polling (Unix LF). Correr: sh start.sh
set -eu

APP_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$APP_DIR"

export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

mkdir -p data logs

if [ ! -f "$APP_DIR/app/__init__.py" ]; then
  echo "ERRO: pasta app/ nao encontrada em $APP_DIR"
  echo "Conteudo:"
  ls -la "$APP_DIR"
  exit 1
fi

echo "Maratona Coach — install deps..."
pip install -r "$APP_DIR/requirements.txt" -q --no-cache-dir

echo "Maratona Coach — registar pacote app..."
pip install --no-deps -e "$APP_DIR" -q --no-cache-dir

echo "Maratona Coach — a arrancar bot..."
if [ -f "$APP_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$APP_DIR/.env"
  set +a
fi
exec python "$APP_DIR/main.py"
