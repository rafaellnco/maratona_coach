# Deploy — JustRunMy.App (polling)

## ANTES DO UPLOAD (obrigatório)

```powershell
cd c:\Users\casa\maratona_coach
.\scripts\stop-bot.ps1
.\scripts\build-deploy-zip.ps1 -BotOnly
```

Para FPS / JustRunMy antigos no painel (**Stop**).

---

## 1. Upload ZIP

Upload de **`maratona-coach-deploy.zip`** (Zip Upload).

O ZIP tem **na raiz** (não dentro de subpasta):

```
app/
main.py
requirements.txt
pyproject.toml
start.sh
.env
```

---

## 2. Start Command — CRÍTICO

No painel JustRunMy, campo **Start Command**, **apaga tudo** e cola **só isto**:

```
sh start.sh
```

**Não uses:**

| Comando | Porquê |
|---------|--------|
| `./start.sh` | Falha permissões |
| `pip install -e .` sozinho | Instala FastAPI pesado (OOM) |
| `python main.py` sem `sh start.sh` | Falta `pip install --no-deps -e .` → `ModuleNotFoundError: app` |
| Comando antigo com `app.entry` | Era webhook |

O `start.sh` faz tudo na ordem certa:

1. `cd` para a pasta do projecto  
2. `pip install -r requirements.txt` (5 pacotes leves)  
3. `pip install --no-deps -e .` (regista o pacote `app` — **fix do erro**)  
4. `python main.py`  

---

## 3. Variáveis de ambiente

Confirma no painel (o ZIP traz `.env`):

| Variável | Valor |
|----------|--------|
| `TELEGRAM_MODE` | `polling` |
| `PYTHONPATH` | `.` |
| `PYTHONUNBUFFERED` | `1` |
| `ANTHROPIC_API_KEY` | preenchido |
| `TELEGRAM_BOT_TOKEN` | preenchido |
| `TELEGRAM_ALLOWED_USER_ID` | teu ID |
| `TELEGRAM_WEBHOOK_URL` | *(vazio)* |
| `PUBLIC_BASE_URL` | *(vazio)* |

---

## 4. Start

1. **Start** (build 5–20 min)
2. **Diagnostics** — deves ver:

```
Maratona Coach — install deps...
Maratona Coach — registar pacote app...
Maratona Coach a arrancar...
Bot Telegram: @... (token OK)
Modo polling activo — bot online 24/7
```

3. Telegram → `/start`

---

## Erro `ModuleNotFoundError: app`

Significa que o Start Command **não** correu `pip install --no-deps -e .`.

**Fix:** Start Command = `sh start.sh` (exactamente) + re-upload do ZIP novo.

---

## Actualizar

```powershell
.\scripts\build-deploy-zip.ps1 -BotOnly
```

Re-upload + confirma Start Command = `sh start.sh` + Restart.
