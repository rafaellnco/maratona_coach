# Deploy fácil — 5 minutos

Sem VM, sem SSH, sem builds Docker, sem cartão.

**Trade-off:** no plano grátis carregas em **Renew** 1× por dia (~10 segundos).

---

## Passo 0 — No teu `.env`

```env
TELEGRAM_ALLOWED_USER_ID=123456789
```

(ID: [@userinfobot](https://t.me/userinfobot))

---

## Passo 1 — Gera o pacote (PowerShell)

```powershell
cd c:\Users\casa\maratona_coach
.\scripts\deploy-facil.ps1
```

Abre o FPS.ms no browser e cria `maratona-fps.zip`.

---

## Passo 2 — Conta + servidor

1. Regista em [fps.ms](https://fps.ms/free-telegram-bot-hosting/)
2. **Create Server** → **Python Telegram Bot**
3. Região: **Netherlands**

---

## Passo 3 — Upload

Painel → **Files** → upload de **`maratona-fps.zip`** → extrai no servidor.

(Tens `app.py`, `.env`, `app/`, `requirements.txt` — o ZIP traz tudo.)

---

## Passo 4 — Start

**Console** → **Start**

Logs:

```
Maratona Coach a arrancar...
Modo polling activo — bot online 24/7
```

Telegram → `/start`

---

## Cada dia (10 segundos)

Painel FPS → botão **Renew** / **+ Add Hours**.

Mete alarme no telemóvel à hora de jantar.

---

## Não funciona?

| Problema | Fix |
|----------|-----|
| Bot não responde | Para JustRunMy/PC — só 1 polling à vez |
| `ModuleNotFoundError` | Re-upload do ZIP completo |
| Expirou | Renew no painel |

---

## Queres zero renew?

Aí só com cartão: Railway (~5€ verificação) ou Oracle (muito setup).  
Para preguiça máxima grátis → **FPS.ms**.
