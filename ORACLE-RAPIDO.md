# Oracle Cloud — guia rápido (com cartão)

24/7 real. Sem renew diário. **0 €** no Always Free.

ZIP pronto: `maratona-oracle.zip`

---

## A. Conta (10 min)

1. [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) → **Start for free**
2. Preenche tudo + **cartão** (verificação, não cobram no free tier)
3. Região home: **Germany (Frankfurt)** ou **France (Paris)**

---

## B. Chave SSH (já no teu PC)

PowerShell — copia a linha que começa com `ssh-ed25519`:

```powershell
Get-Content "$env:USERPROFILE\.ssh\oracle_maratona.pub"
```

---

## C. VM (5 min)

1. Menu ☰ → **Compute** → **Instances** → **Create instance**
2. Nome: `maratona-coach`
3. Image: **Ubuntu 24.04**
4. Shape: **Change shape** → **Ampere** → **VM.Standard.A1.Flex** → 1 OCPU, 6 GB RAM
5. **Public IPv4** ✓
6. **SSH keys** → cola a chave pública do passo B
7. **Create**

> **Out of capacity?** Tenta outra região ou horário.

### Abrir SSH (só 1×)

**Networking** → **Virtual cloud networks** → VCN default → **Security Lists** → **Default** → **Add Ingress Rule**:

- Source: `0.0.0.0/0`
- TCP port: **22**

Copia o **Public IP** da instância.

---

## D. Upload (2 min)

Substitui `TEU_IP`:

```powershell
cd c:\Users\casa\maratona_coach
scp -i "$env:USERPROFILE\.ssh\oracle_maratona" maratona-oracle.zip ubuntu@TEU_IP:~/
```

---

## E. Instalar (2 min)

```powershell
ssh -i "$env:USERPROFILE\.ssh\oracle_maratona" ubuntu@TEU_IP
```

Dentro da VM:

```bash
sudo apt-get update && sudo apt-get install -y unzip
unzip -o maratona-oracle.zip -d maratona_coach
cd maratona_coach && bash install.sh
```

---

## F. Testar

```bash
journalctl -u maratona-coach -f
```

Vês `Modo polling activo` → Telegram `/start`

---

## Comandos úteis

```bash
sudo systemctl restart maratona-coach   # reiniciar
sudo systemctl status maratona-coach    # estado
```

Para o JustRunMy/FPS/PC antes — **só 1 bot a fazer polling**.
