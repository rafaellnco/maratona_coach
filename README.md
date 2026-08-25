# Maratona Coach

Backend Python para **AI Telegram Coach** — treinador de corrida de elite e nutricionista desportivo powered by Claude (Anthropic).

## Stack

- **FastAPI** — API REST
- **SQLModel** + **SQLite** — perfil, plano 14 semanas, logs diários
- **Anthropic Claude** — tool use (`update_daily_log`, `get_training_plan`)
- **Telegram Bot API** — mensagens
- **APScheduler** — notificações 09:00 e 22:30

## Configuração local

### 1. Bot no Telegram

1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copia o token → `TELEGRAM_BOT_TOKEN` no `.env`

### 2. Projecto

```powershell
cd c:\Users\casa\maratona_coach
python -m venv .venv
.venv\Scripts\activate
pip install -e .
copy .env.example .env
```

Edita `.env`: `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, e opcionalmente `TELEGRAM_ALLOWED_USER_ID` (ID via [@userinfobot](https://t.me/userinfobot) — **só tu usas o bot**).

### 3. Arrancar (teste local — polling)

```powershell
python main.py
```

Envia `/start` no Telegram. Exemplos: *"corri 10km hoje"*, *"qual é o plano completo?"*

Local usa **polling** (`python main.py`). JustRunMy: ver [JUSTRUNMYAPP.md](JUSTRUNMYAPP.md).

## Deploy 24/7 (sem PC ligado)

👉 **[ORACLE-RAPIDO.md](ORACLE-RAPIDO.md)** — Oracle Always Free (cartão só verificação, 24/7 real)

```powershell
.\scripts\build-oracle-zip.ps1
```

Alternativa sem cartão: [FACIL.md](FACIL.md) (FPS.ms, renew 10 s/dia)

## Showcase (página para amigos)

Abre localmente: `docs/showcase.html`

No JustRunMy, re-upload do ZIP completo (sem `-BotOnly`) + porta HTTPS **8080**.

## Testes

```powershell
pip install -e ".[dev]"
pytest
```
