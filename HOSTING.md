# Hosting 24/7 — alternativas ao JustRunMy.App

O JustRunMy usa builds Docker automáticos que falham muito. Estas opções **não** passam por isso.

---

## Opção A — Oracle Cloud Always Free (recomendado)

24/7 de verdade, sem renovar. Cartão só para verificação.

👉 Guia completo: **[ORACLE.md](ORACLE.md)**

```powershell
.\scripts\build-oracle-zip.ps1
```

---

## Opção B — FPS.ms (sem cartão)

Feito para bots Telegram. Upload de ficheiros → **Start**. Sem builds AI.

### Passo 1 — Parar tudo o resto

Só pode haver **uma** instância a fazer polling:

```powershell
cd c:\Users\casa\maratona_coach
.\scripts\stop-bot.ps1
```

Para o JustRunMy.App no painel (**Stop**) se ainda tiveres serviço lá.

### Passo 2 — Conta e servidor

1. [fps.ms/free-telegram-bot-hosting](https://fps.ms/free-telegram-bot-hosting/) → regista
2. **Create Server** → **Python Telegram Bot**
3. Região: **Netherlands** (The Hague)

### Passo 3 — Gerar pacote

```powershell
cd c:\Users\casa\maratona_coach
.\scripts\build-fps-zip.ps1
```

Cria `maratona-fps.zip` (~32 KB) com `.env` incluído.

### Passo 4 — Upload

Painel → **Files** → upload destes ficheiros (extrai o ZIP ou envia um a um):

| Ficheiro | Obrigatório |
|----------|-------------|
| `app.py` | ✓ |
| `requirements.txt` | ✓ |
| `.env` | ✓ |
| pasta `app/` | ✓ |
| `pyproject.toml` | ✓ |

### Passo 5 — Startup

Tab **Startup** → ficheiro principal: **`app.py`** (default)

Tab **Console** → **Start**

Logs esperados:

```
Maratona Coach a arrancar...
Modo polling activo — bot online 24/7
Scheduler iniciado — briefing 09:00, recovery 22:30
```

Telegram → `/start`

### Renovar a cada 24h (plano free)

Painel → botão **Renew** / **+ Add Hours** (~10 s).  
Mete alarme no telemóvel. Ficheiros ficam 28 dias se expirar.

### `.env` mínimo

```env
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_ID=123456789
DATABASE_URL=sqlite:///./data/maratona_coach.db
SCHEDULER_TIMEZONE=Europe/Lisbon
APP_ENV=production
SHOWCASE_ENABLED=false
PYTHONPATH=.
```

---

## Opção C — JustRunMy.App (polling — recomendado)

Ver [JUSTRUNMYAPP.md](JUSTRUNMYAPP.md). Start Command:

```
sh start.sh
```

---

## Erros comuns (FPS.ms)

| Erro | Solução |
|------|---------|
| `can't open file app.py` | `app.py` na raiz do servidor |
| `ModuleNotFoundError: app` | Upload pasta `app/` + `PYTHONPATH=.` |
| Bot não responde | Conflict polling — para PC local e JustRunMy |
| `Unauthorized` | Token errado no `.env` |
| Crash por memória | `SHOWCASE_ENABLED=false` (já no ZIP) |

Documentação FPS: [docs.fps.ms/telegram-bots](https://docs.fps.ms/telegram-bots)
