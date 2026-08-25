#!/bin/bash
# Instala Maratona Coach como serviço systemd (Oracle Cloud Always Free)
# Corre dentro da pasta do projecto: bash install.sh

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="maratona-coach"
PY=""

log() { echo "[install] $*"; }

pick_python() {
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" &>/dev/null; then
      version=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
      major=${version%%.*}
      minor=${version#*.}
      if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
        PY=$candidate
        return 0
      fi
    fi
  done
  return 1
}

install_python312() {
  log "A instalar Python 3.12 (projecto requer 3.11+)..."
  sudo apt-get update -qq
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update -qq
  sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
  PY=python3.12
}

log "Directório: $APP_DIR"
cd "$APP_DIR"

if [ ! -f ".env" ]; then
  echo "ERRO: .env não encontrado em $APP_DIR"
  echo "Gera o ZIP no PC com: .\\scripts\\build-oracle-zip.ps1"
  exit 1
fi

sudo apt-get update -qq
sudo apt-get install -y unzip curl

if pick_python; then
  log "Python: $PY ($($PY --version))"
else
  install_python312
fi

mkdir -p "$APP_DIR/data"

if [ -d ".venv" ]; then
  log "A remover venv antigo..."
  rm -rf .venv
fi

"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/pip install -q -e .

# Garantir DATABASE_URL correcto para produção
if grep -q '^DATABASE_URL=' .env; then
  sed -i 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///'"$APP_DIR"'/data/maratona_coach.db|' .env
else
  echo "DATABASE_URL=sqlite:///$APP_DIR/data/maratona_coach.db" >> .env
fi

grep -q '^SHOWCASE_ENABLED=' .env || echo "SHOWCASE_ENABLED=false" >> .env
grep -q '^APP_ENV=' .env || echo "APP_ENV=production" >> .env
grep -q '^PYTHONPATH=' .env || echo "PYTHONPATH=." >> .env

sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Maratona Coach Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${APP_DIR}
Environment=PYTHONPATH=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

sleep 2
sudo systemctl status "${SERVICE_NAME}" --no-pager || true

echo ""
echo "============================================"
echo " Maratona Coach instalado!"
echo " Logs:  journalctl -u ${SERVICE_NAME} -f"
echo " Parar: sudo systemctl stop ${SERVICE_NAME}"
echo " Teste: envia /start no Telegram"
echo "============================================"
