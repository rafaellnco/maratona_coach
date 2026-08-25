# Deploy Oracle Cloud Always Free — 24/7 sem renovar

VM grátis para sempre (4 ARM cores / 24 GB RAM no total). Cartão **só para verificação** — não cobram se ficares no Always Free.

---

## Parte 1 — Conta Oracle (~15 min)

1. [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) → **Start for free**
2. Preenche dados + **cartão** (verificação ~1€ temporário, devolvido)
3. Escolhe região **home** perto de ti: ex. **Germany Central (Frankfurt)** ou **France Central (Paris)**
4. Confirma email

---

## Parte 2 — Criar a VM (~10 min)

No **Oracle Cloud Console**:

### 2.1 Rede (só 1× na conta)

1. Menu ☰ → **Networking** → **Virtual cloud networks**
2. Clica na VCN default (ou cria uma)
3. **Security Lists** → **Default Security List** → **Add Ingress Rules**
4. Adiciona:
   - Source: `0.0.0.0/0` (ou só o teu IP por segurança)
   - IP Protocol: **TCP**
   - Destination Port: **22**
   - Description: `SSH`

> O bot usa **polling** (liga ao Telegram). Não precisas abrir portas 80/443.

### 2.2 Chave SSH no Windows

PowerShell:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\oracle_maratona" -N '""'
Get-Content "$env:USERPROFILE\.ssh\oracle_maratona.pub"
```

Copia a linha `.pub` — vais colar na Oracle.

### 2.3 Criar instância

1. Menu ☰ → **Compute** → **Instances** → **Create instance**
2. Nome: `maratona-coach`
3. **Image:** Ubuntu 24.04 (ou 22.04)
4. **Shape:** **Ampere** → **VM.Standard.A1.Flex**
   - OCPUs: **1**
   - Memory: **6 GB** (sobra para o bot)
5. **Networking:** mesma VCN/subnet pública
6. **Assign a public IPv4 address:** ✓
7. **SSH keys:** cola a chave pública do passo 2.2
8. **Create**

Espera estado **Running**. Copia o **Public IP** (ex. `123.45.67.89`).

> Se der **Out of capacity** na região, tenta outra região Always Free ou volta mais tarde.

---

## Parte 3 — Preparar ZIP no PC

Confirma no `.env`:

```env
TELEGRAM_ALLOWED_USER_ID=123456789
```

(ID via [@userinfobot](https://t.me/userinfobot))

```powershell
cd c:\Users\casa\maratona_coach
.\scripts\stop-bot.ps1
.\scripts\build-oracle-zip.ps1
```

Cria `maratona-oracle.zip`.

Para JustRunMy/FPS/local — **para tudo** antes (só 1 polling activo).

---

## Parte 4 — Upload para a VM

Substitui `123.45.67.89` pelo teu IP:

```powershell
scp -i "$env:USERPROFILE\.ssh\oracle_maratona" `
  c:\Users\casa\maratona_coach\maratona-oracle.zip `
  ubuntu@123.45.67.89:~/
```

Primeira ligação SSH:

```powershell
ssh -i "$env:USERPROFILE\.ssh\oracle_maratona" ubuntu@123.45.67.89
```

---

## Parte 5 — Instalar na VM

Dentro da VM (SSH):

```bash
sudo apt-get update && sudo apt-get install -y unzip
unzip -o maratona-oracle.zip -d maratona_coach
cd maratona_coach
chmod +x install.sh
bash install.sh
```

Instala Python, dependências, serviço **systemd**. Arranca automaticamente no reboot.

Logs em tempo real:

```bash
journalctl -u maratona-coach -f
```

Procurar:

```
Modo polling activo — bot online 24/7
Scheduler iniciado — briefing 09:00, recovery 22:30
```

Telegram → `/start`

---

## Comandos úteis (na VM)

| Acção | Comando |
|--------|---------|
| Ver logs | `journalctl -u maratona-coach -f` |
| Estado | `sudo systemctl status maratona-coach` |
| Reiniciar | `sudo systemctl restart maratona-coach` |
| Parar | `sudo systemctl stop maratona-coach` |

---

## Actualizar o bot (novo código)

No PC:

```powershell
.\scripts\build-oracle-zip.ps1
scp -i "$env:USERPROFILE\.ssh\oracle_maratona" maratona-oracle.zip ubuntu@IP:~/
```

Na VM:

```bash
cd ~/maratona_coach
# backup opcional da BD
cp data/maratona_coach.db data/maratona_coach.db.bak 2>/dev/null || true
cd ~
unzip -o maratona-oracle.zip -d maratona_coach
cd maratona_coach && bash install.sh
```

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| SSH timeout | Confirma regra porta 22 na Security List; IP público assignado |
| `Out of capacity` | Outra região ou tentar de manhã |
| Bot não responde | `journalctl -u maratona-coach -n 50`; para PC/JustRunMy/FPS |
| `Conflict: terminated by other getUpdates` | Só 1 instância polling — para as outras |
| Python < 3.11 | O `install.sh` instala 3.12 via PPA automaticamente |

---

## Custo

Recursos Always Free dentro dos limites = **0 €/mês**.  
Não cries recursos paid sem querer (Load Balancer paid, etc.).
